import json
from flask import Flask, request, jsonify, Response
from better_profanity import profanity
import boto3
import codecs

app = Flask(__name__)

@app.route('/')

def lambda_handler(event, context):
    # Initialize AWS services
    comprehend = boto3.client('comprehend')
    translate = boto3.client('translate')
    # Get input text from event
    input_text = event['text']
    
    # Determine input text language
    detect_result = comprehend.detect_dominant_language(Text=input_text)
    input_language = detect_result['Languages'][0]['LanguageCode']
    
    # If input text is Japanese, translate to English and detect PII
    if input_language != 'en':
        # Translate to English
        translate_result = translate.translate_text(
            Text=input_text, 
            SourceLanguageCode='auto',
            TargetLanguageCode='en',
            )
        english_text = translate_result['TranslatedText']
    else:
        english_text = input_text

        # Detect PII in English text
    pii_result = comprehend.detect_pii_entities(Text=english_text, LanguageCode='en')
        
        # Redact PII in English text
    redacted_text = redact_pii_entities(english_text, pii_result['Entities'])
        
         # Mask profanity using better_profanity library
    profane_text = mask_profanity(redacted_text)

        # Translate redacted English text back to Japanese
    if input_language != 'en':
        translate_result = translate.translate_text(
            Text= profane_text, 
            SourceLanguageCode='en', 
            TargetLanguageCode=input_language
            )
        
        output_text = translate_result['TranslatedText']
        
    else:
        output_text = profane_text
  
    # Return output text
    return {
        'text': output_text
    }

def redact_pii_entities(text, entities):
    """
    Redacts PII entities in text by replacing them with 'REDACTED'.
    """

    for NER in reversed(entities):
        text = text[:NER['BeginOffset']] + "****" + text[NER['EndOffset']:]
    return{
    
        "body": json.dumps(text)
    }

def mask_profanity(text):
    
   # Masks profanity in text using Better Profanity.

    profanity.load_censor_words()
    profane_text = profanity.censor(text)
    return profane_text

if __name__ == '__main__':
    app.run(debug=True)