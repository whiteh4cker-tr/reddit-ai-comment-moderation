import praw
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
import re

# Reddit API credentials
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="YOUR_USER_AGENT",
    username="YOUR_REDDIT_USERNAME",
    password="YOUR_REDDIT_PASSWORD"
)

# Load the models and tokenizers
translation_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tc-big-tr-en")
translation_model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-tc-big-tr-en")
moderation_tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation")
moderation_model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation")

# Subreddit to monitor
subreddit_name = "subredditname"

# Regular expression to match Turkish characters
turkish_chars_regex = re.compile(r'[çğıöşüÇĞİÖŞÜ]')

def has_turkish_chars(text):
    """Check if the text contains Turkish characters."""
    return bool(turkish_chars_regex.search(text))

def translate_text(text, max_length=510):
    """Translate Turkish text to English."""
    inputs = translation_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
    # max_length += inputs.input_ids.size(1)  # Add the length of input sequence to max_length
    outputs = translation_model.generate(inputs.input_ids, max_length=max_length, num_beams=4, early_stopping=True)
    translated_text = translation_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return translated_text

def moderate_comments():
    subreddit = reddit.subreddit(subreddit_name)
    while True:
        try:
            # Check new comments continuously
            for comment in subreddit.stream.comments(skip_existing=True):
                try:
                    if has_turkish_chars(comment.body):
                        # Translate Turkish comments to English
                        translated_comment = translate_text(comment.body)
                        inputs_translated = moderation_tokenizer(translated_comment, return_tensors="pt")
                        print("Translated Text:", translated_comment)  # Print translated text
                    else:
                        translated_comment = None
                    
                    # Apply moderation model to original comment
                    inputs_original = moderation_tokenizer(comment.body, return_tensors="pt", truncation=True, max_length=510)
                    
                    outputs_original = moderation_model(**inputs_original)
                    probabilities_original = outputs_original.logits.softmax(dim=-1).squeeze()
                    id2label = moderation_model.config.id2label
                    labels_original = [id2label[idx] for idx in range(len(probabilities_original))]
                    label_prob_pairs_original = list(zip(labels_original, probabilities_original))
                    label_prob_pairs_original.sort(key=lambda item: item[1], reverse=True)
                    
                    # Apply moderation model to translated comment if it exists
                    if translated_comment:
                        outputs_translated = moderation_model(**inputs_translated)
                        probabilities_translated = outputs_translated.logits.softmax(dim=-1).squeeze()
                        labels_translated = [id2label[idx] for idx in range(len(probabilities_translated))]
                        label_prob_pairs_translated = list(zip(labels_translated, probabilities_translated))
                        label_prob_pairs_translated.sort(key=lambda item: item[1], reverse=True)
                    
                    # Check if any label other than "OK" has probability >= 0.75 for either original or translated comment
                    should_remove = False
                    should_approve = False
                    for label, probability in label_prob_pairs_original:
                        if label != "OK" and probability >= 0.75:
                            should_remove = True
                            break
                    if not should_remove and translated_comment:
                        for label, probability in label_prob_pairs_translated:
                            if label != "OK" and probability >= 0.75:
                                should_remove = True
                                break

                    # Check if "OK" label has probability >= 0.97 for either original or translated comment
                    if not should_remove:
                        for (label_orig, probability_orig), (label_trans, probability_trans) in zip(label_prob_pairs_original, label_prob_pairs_translated):
                            if label_orig == "OK" and label_trans == "OK" and probability_orig >= 0.97 and probability_trans >= 0.97:
                                should_approve = True
                                break

                    # Print and remove comment if necessary
                    if should_remove:
                        print("Removing comment with label:", label, "and probability:", probability)
                        print("Removed comment:", comment.body)  # Print original text
                        if translated_comment:
                            print("Removed comment translation:", translated_comment)  # Print translated text
                        comment.mod.remove()

                        # Add moderator note
                        reddit.subreddit(subreddit_name).mod.notes.create(label="ABUSE_WARNING", note="Violation", redditor=comment.author)
                    
                    # Print and approve comment if necessary
                    if should_approve:
                        print("Approved comment:", comment.body)  # Print original text
                        if translated_comment:
                            print("Approved comment translation:", translated_comment)  # Print translated text
                        comment.mod.approve()

                    else:
                        print("Comment is processed, but no action is taken. Content:", comment.body)
                        print("Comment is processed, but no action is taken. Translated Text:", translated_comment)
                except Exception as e:
                    print("Error processing comment:", e)
        except Exception as e:
            print("Error processing comment:", e)

if __name__ == "__main__":
    moderate_comments()