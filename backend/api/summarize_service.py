import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from collections import defaultdict
import re
import os
import torch
from pathlib import Path

# Updated NLTK data checking and downloading
nltk_data_dir = Path(os.getenv("NLTK_DATA", Path.home() / 'nltk_data'))

def ensure_nltk_resources():
    """Ensure all required NLTK resources are available"""
    try:
        # Try to download the specific punkt_tab resource that's missing
        nltk.download('punkt_tab')
    except:
        # If that fails, try the standard punkt resource
        nltk.download('punkt')
    
    try:
        nltk.download('stopwords')
    except Exception as e:
        print(f"Error downloading stopwords: {e}")

# Call this at module import time
ensure_nltk_resources()

# Try to import transformers for advanced summarization
TRANSFORMERS_AVAILABLE = False
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

def extract_keywords(text, num_keywords=8):
    """
    Extract key terms from the article to include in the summary.
    
    Args:
        text (str): The article text
        num_keywords (int): Number of keywords to extract
        
    Returns:
        list: List of keywords
    """
    try:
        # Convert to lowercase and remove non-alphanumeric characters
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Try to tokenize words, with fallback
        try:
            words = word_tokenize(text)
        except LookupError:
            # Simple fallback tokenization if NLTK tokenizer fails
            words = text.split()
        
        # Remove stopwords, with fallback if stopwords not available
        try:
            stop_words = set(stopwords.words('english'))
        except:
            # Basic stopwords if NLTK stopwords unavailable
            stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 
                         'what', 'when', 'where', 'how', 'who', 'which', 'this', 'that', 
                         'to', 'in', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                         'have', 'has', 'had', 'do', 'does', 'did', 'of', 'for', 'with'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Calculate word frequencies
        fdist = FreqDist(filtered_words)
        
        # Get most common words
        return [word for word, _ in fdist.most_common(num_keywords)]
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return ["news", "market", "company", "stock", "business"]  # Fallback keywords

def simple_sentence_tokenize(text):
    """
    Simple sentence tokenization as fallback if NLTK tokenizer fails.
    
    Args:
        text (str): Text to tokenize into sentences
        
    Returns:
        list: List of sentences
    """
    # More sophisticated regex-based sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    # Filter out empty or very short sentences
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

def extract_important_sentences(text, keywords, max_sentences=4, title_text=""):
    """
    Extract the most important sentences based on keywords and position.
    Also ensures minimal overlap with the title content.
    
    Args:
        text (str): The article text
        keywords (list): List of keywords
        max_sentences (int): Maximum number of sentences to include
        title_text (str): The title text to avoid redundancy
        
    Returns:
        list: List of important sentences
    """
    try:
        # Try NLTK's sentence tokenizer first
        try:
            sentences = sent_tokenize(text)
        except LookupError:
            # Fall back to simple tokenization if NLTK fails
            sentences = simple_sentence_tokenize(text)
        
        # If no sentences were extracted or too few, fall back to paragraph-based approach
        if len(sentences) < 3 and len(text) > 200:
            # Split by double newlines (paragraphs) and then by sentences
            paragraphs = re.split(r'\n\s*\n', text)
            sentences = []
            for para in paragraphs:
                try:
                    para_sentences = sent_tokenize(para)
                except:
                    para_sentences = simple_sentence_tokenize(para)
                sentences.extend(para_sentences)
        
        # If still no sentences and text exists, create basic sentences
        if not sentences and text:
            # Split by periods and ensure each "sentence" isn't too long
            raw_sentences = text.split('.')
            sentences = []
            for s in raw_sentences:
                if len(s.strip()) > 10:  # Only include if somewhat substantial
                    sentences.append(s.strip() + '.')
        
        # Convert title to lowercase for comparison
        title_lower = title_text.lower()
        title_words = set(re.findall(r'\b\w+\b', title_lower))
        
        # Score sentences based on multiple factors
        sentence_scores = defaultdict(int)
        
        for i, sentence in enumerate(sentences):
            # Clean sentence (lowercase)
            clean_sentence = sentence.lower()
            sentence_words = set(re.findall(r'\b\w+\b', clean_sentence))
            
            # Calculate overlap with title (penalize high overlap)
            if title_words and len(title_words) > 0:
                overlap_ratio = len(sentence_words.intersection(title_words)) / len(title_words)
                # Penalize sentences that are too similar to the title
                if overlap_ratio > 0.7:  # More than 70% overlap
                    sentence_scores[i] -= 5
                elif overlap_ratio > 0.5:  # More than 50% overlap
                    sentence_scores[i] -= 3
                elif overlap_ratio < 0.2:  # Less than 20% overlap (good, provides new info)
                    sentence_scores[i] += 2
            
            # Score based on keyword presence (weighted by keyword importance)
            for j, keyword in enumerate(keywords):
                keyword_weight = len(keywords) - j  # Higher weight for more important keywords
                if keyword in clean_sentence:
                    sentence_scores[i] += keyword_weight
            
            # Position-based scoring
            if i == 0:  # First sentence (most important)
                sentence_scores[i] += 5
            elif i == 1:  # Second sentence
                sentence_scores[i] += 3
            elif i < len(sentences) // 3:  # First third of the article
                sentence_scores[i] += 2
            elif i > len(sentences) * 2 // 3:  # Last third of the article (conclusions)
                sentence_scores[i] += 1
                
            # Length-based scoring (prefer medium-length sentences)
            words_count = len(sentence.split())
            if 10 <= words_count <= 25:  # Ideal sentence length
                sentence_scores[i] += 2
            elif words_count < 5:  # Too short
                sentence_scores[i] -= 2
            elif words_count > 40:  # Too long
                sentence_scores[i] -= 1
                
            # Contains numbers or specific data points
            if re.search(r'\d+%|[$€£¥]\d+|\d+\.\d+', sentence):
                sentence_scores[i] += 2
                
        # Get top-scoring sentences while ensuring we don't exceed max_sentences
        top_sentence_indices = sorted(
            [i for i in sentence_scores], 
            key=lambda idx: sentence_scores[idx], 
            reverse=True
        )[:max_sentences]
        
        # Always include the first sentence if it's not already included,
        # is not too short, and doesn't overlap too much with the title
        if 0 not in top_sentence_indices and len(sentences) > 0 and len(sentences[0].split()) >= 5:
            # Check title overlap for first sentence
            first_sentence_words = set(re.findall(r'\b\w+\b', sentences[0].lower()))
            if title_words:
                overlap = len(first_sentence_words.intersection(title_words)) / len(title_words)
                if overlap < 0.6:  # Include only if overlap is less than 60%
                    if len(top_sentence_indices) >= max_sentences:
                        # Replace the lowest-scoring sentence
                        min_score_idx = min(top_sentence_indices, key=lambda idx: sentence_scores[idx])
                        top_sentence_indices.remove(min_score_idx)
                    top_sentence_indices.append(0)
        
        # Sort by position in article to maintain flow
        top_sentence_indices.sort()
        
        # Return sentences
        selected_sentences = [sentences[i] for i in top_sentence_indices]
        
        # Ensure sentences end with proper punctuation
        for i, sentence in enumerate(selected_sentences):
            if not sentence.strip().endswith(('.', '!', '?')):
                selected_sentences[i] = sentence.strip() + '.'
        
        return selected_sentences
    except Exception as e:
        print(f"Error extracting important sentences: {e}")
        # If all else fails, just return the first part of the text
        if text:
            # Try to get a complete first sentence
            first_period = text.find('.')
            if 10 < first_period < 300:
                return [text[:first_period+1]]
            return [text[:200].strip() + "..."]
        return ["No important sentences found."]

def format_summary(sentences, company_name=None):
    """
    Format the extracted sentences into a coherent summary.
    No longer adds "Regarding [company_name]" prefix.
    
    Args:
        sentences (list): List of important sentences
        company_name (str, optional): Company name for context
        
    Returns:
        str: Formatted summary
    """
    if not sentences:
        return "No summary available."
    
    # Join sentences with proper spacing
    raw_summary = ' '.join(sentences)
    
    # Clean up spacing issues
    summary = re.sub(r'\s+', ' ', raw_summary).strip()
    
    # Ensure summary has proper capitalization
    if summary and summary[0].islower():
        summary = summary[0].upper() + summary[1:]
    
    # Remove double periods
    summary = re.sub(r'\.\.', '.', summary)
    
    # Ensure it ends with proper punctuation
    if summary and not summary.endswith(('.', '!', '?')):
        summary = summary + '.'
    
    return summary

def summarize_with_transformers(text, company_name=None, title_text=""):
    """
    Use Hugging Face transformers for summarization if available.
    Modified to avoid adding "Regarding [company_name]" prefix.
    
    Args:
        text (str): Text to summarize
        company_name (str, optional): Company name for context
        title_text (str): The title text to check for redundancy
        
    Returns:
        str: Summarized text or None if transformers not available
    """
    if not TRANSFORMERS_AVAILABLE:
        return None
        
    try:
        # Check if CUDA is available for faster processing
        device = 0 if torch.cuda.is_available() else -1
        
        # Create summarization pipeline
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
        
        # Process text (handle length limitations - max 1024 tokens for most models)
        if len(text) > 5000:
            text = text[:5000]  # Truncate to avoid issues
            
        # Generate summary
        result = summarizer(text, max_length=150, min_length=60, do_sample=False)
        
        if result and len(result) > 0:
            summary = result[0]['summary_text']
            
            # Clean up the transformer summary
            summary = summary.strip()
            
            # Ensure proper capitalization
            if summary and summary[0].islower():
                summary = summary[0].upper() + summary[1:]
                
            # Ensure it ends with proper punctuation
            if not summary.endswith(('.', '!', '?')):
                summary = summary + '.'
                
            return summary
    except Exception as e:
        print(f"Transformer summarization error: {e}")
    
    return None

# Changes to summarize_service.py

# 1. Improve clean_article_text function to remove more boilerplate
def clean_article_text(text):
    """
    Clean article text by removing common boilerplate content.
    
    Args:
        text (str): The article text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # More aggressive removal of common boilerplate phrases
    boilerplate_patterns = [
        # Visit website phrases
        r'(For more information|To learn more|For further details|Read more|Find out more|Click here for more)(.+?)(website|site|page|URL).*?\.', 
        r'Visit\s+.+?\s+for\s+more\s+.*?\.', 
        r'Click\s+here\s+to\s+.*?\.', 
        r'Learn\s+more\s+at\s+.*?\.', 
        
        # Generic calls to action
        r'Find\s+out\s+more\s+.*?\.', 
        r'Learn\s+more\s+.*?\.', 
        r'See\s+more\s+.*?\.', 
        r'Read\s+the\s+full\s+.*?\.', 
        r'Follow\s+this\s+link\s+.*?\.', 
        
        # Subscription prompts
        r'Subscribe\s+to\s+our\s+newsletter.*?\.', 
        r'Sign\s+up\s+for\s+our\s+.*?\.', 
        r'Get\s+updates\s+.*?\.', 
        
        # Copyright notices
        r'©\s*\d{4}.*?\.\s*', 
        r'Copyright\s*©.*?\.\s*', 
        
        # Social media prompts
        r'Follow\s+us\s+on\s+.*?\.', 
        r'Like\s+us\s+on\s+.*?\.', 
        r'Share\s+this\s+.*?\.', 
        
        # End-of-article indicators
        r'The\s+content\s+is\s+provided\s+for\s+information\s+purposes\s+only.*?\.', 
        r'All\s+rights\s+reserved.*?\.', 
        r'This\s+article\s+was\s+originally\s+published\s+.*?\.', 
    ]
    
    # Apply all patterns
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces and line breaks
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# 2. Improve enhance_title to remove redundant company mentions
def enhance_title(title, max_length=75):
    """
    Makes article titles more concise and clean by removing stock tickers,
    unnecessary prefixes, and ensuring completeness.
    
    Args:
        title (str): The original article title
        max_length (int): Maximum target length for the enhanced title
        
    Returns:
        str: Enhanced, more concise title
    """
    # Return original if title is empty 
    if not title:
        return title
    
    # Store original title for comparison
    original_title = title
    
    # Step 1: Remove stock ticker patterns: (NASDAQ:NVDA), (NYSE:AAPL), etc.
    title = re.sub(r'\s*\([A-Z]+:[A-Z]+\)', '', title)
    
    # Step 2: Remove redundant prefixes
    redundant_prefixes = [
        "BREAKING: ", "Breaking: ", "UPDATE: ", "Update: ", "EXCLUSIVE: ", "Exclusive: ",
        "REPORT: ", "Report: ", "WATCH: ", "Watch: ", "JUST IN: ", "Just In: ",
        "VIDEO: ", "Video: ", "ANALYSIS: ", "Analysis: ", "FEATURED: ", "Featured: ",
        "ALERT: ", "Alert: ", "TRENDING: ", "Trending: "
    ]
    
    for prefix in redundant_prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    
    # Step 3: Clean up trailing ellipses and other punctuation
    title = re.sub(r'\.{3,}$', '', title.strip())
    title = re.sub(r'\s*\.\.\.$', '', title)
    
    # Step 4: Strip excess whitespace
    title = ' '.join(title.split())
    
    # Step 5: Remove specific phrases that add little value
    filler_phrases = [
        " according to sources", " according to reports", " according to insiders",
        " sources say", " reports indicate", " experts say", " analysts believe",
        ", experts say", ", analysts say", ", sources say", ", reports indicate",
        " - report", " - sources", " - analysts", " - insiders", " report claims",
        " analysts report", " sources claim", ", report says", ", report claims"
    ]
    
    for phrase in filler_phrases:
        if phrase in title.lower():
            title = title.replace(phrase, "")
            title = title.replace(phrase.capitalize(), "")
    
    # Step 6: Ensure first character is capitalized
    if title and title[0].islower():
        title = title[0].upper() + title[1:]
    
    # NEW - Check for and remove redundant company mentions
    # Extract common company names that might appear redundantly
    common_companies = ["Amazon", "Amazon.com", "Apple", "Microsoft", "Google", "Meta", 
                        "Facebook", "Tesla", "Nvidia", "Broadcom", "Alphabet"]
    
    for company in common_companies:
        # Check if company appears at start AND end of title
        company_lower = company.lower()
        title_lower = title.lower()
        
        # If company is at beginning AND end (allowing for some words in between at the end)
        if title_lower.startswith(company_lower) and (
                title_lower.endswith(company_lower) or 
                re.search(rf'{company_lower}(\s+\w+){{1,3}}$', title_lower)):
            
            # Remove from end (with the last few words if they exist)
            end_match = re.search(rf'(,?\s+|-\s+)({company_lower}(\s+\w+){{0,3}})$', title_lower)
            if end_match:
                end_start = end_match.start()
                title = title[:end_start]
                
                # Make sure it ends with proper punctuation
                if not title.endswith(('.', '!', '?')):
                    title = title + '.'
                    
                # Cleanup any trailing commas, dashes, or spaces
                title = re.sub(r'[,\s-]+\.$', '.', title)
    
    # If title is now concise enough, return it
    if len(title) <= max_length:
        return title
    
    # Rest of the function remains unchanged...
    try:
        # 7a: If title has a colon, consider using the more informative part
        if ': ' in title:
            parts = title.split(': ', 1)
            # Determine which part is more informative
            if len(parts[1]) > 25 and parts[1].count(' ') >= 3:  # Ensure it's substantial
                # Check if part after colon forms a complete thought
                if parts[1][0].isupper() and any(parts[1].endswith(p) for p in ['.', '!', '?', '"']):
                    return parts[1]
                else:
                    # Check if combining with the first part makes sense
                    first_word = parts[0].split()[-1].lower()
                    if first_word in ['says', 'states', 'reports', 'announces', 'confirms', 'reveals']:
                        # Use format: "[Company] [verb]: [information]"
                        company_part = ' '.join(parts[0].split()[:-1])
                        if len(company_part) > 0:
                            combined = f"{company_part} {first_word}: {parts[1]}"
                            if len(combined) <= max_length:
                                return combined
                    return parts[1]
            elif len(parts[0]) > 25 and parts[0].count(' ') >= 3:
                return parts[0]
        
        # 7b: Handle dash-separated titles
        for separator in [' - ', ' – ', ' — ']:
            if separator in title:
                parts = title.split(separator, 1)
                # Check which part is more informative
                if len(parts[0]) >= 30 and parts[0].count(' ') >= 3:
                    return parts[0]
                elif len(parts[1]) >= 30 and parts[1].count(' ') >= 3:
                    return parts[1]
        
        # 7c: If still too long, try to find a natural breakpoint
        if len(title) > max_length:
            # Try to break at key conjunctions or punctuation
            shortened = title[:max_length-1]
            
            # Look for natural break points
            break_points = []
            for pattern in [r'(?<=[.!?]) ', r', ', r'; ', r' but ', r' and ', r' as ', r' due to ']:
                for match in re.finditer(pattern, shortened):
                    break_points.append(match.end())
            
            if break_points:
                # Get the last good break point
                break_points.sort(reverse=True)
                for point in break_points:
                    if point > max_length * 0.65:  # Use break point if we keep at least 65% of max length
                        candidate = title[:point].strip()
                        # Ensure it ends with proper punctuation
                        if not candidate.endswith(('.', '!', '?')):
                            candidate += '.'
                        # Make sure it's not just cutting the original title in half
                        if len(candidate) >= max_length * 0.7 and candidate != original_title[:len(candidate)]:
                            return candidate
            
            # If no good break points found, try to find the last complete word
            last_space = shortened.rfind(' ')
            if last_space > max_length * 0.8:  # Only truncate if we can keep 80% of max_length
                shortened = title[:last_space]
                # Ensure it ends with proper punctuation
                if not shortened.endswith(('.', '!', '?')):
                    shortened += '.'
                return shortened
    
    except Exception as e:
        print(f"Error enhancing title: {e}")
    
    # If all else fails, keep the original title if it's not too much longer than max_length
    if len(original_title) <= max_length * 1.25:  # Only 25% longer than target
        return original_title
    
    # Absolute fallback: Just truncate at max_length with a word boundary
    shortened = title[:max_length-3]
    last_space = shortened.rfind(' ')
    if last_space > 0:
        return shortened[:last_space] + '...'
    return shortened + '...'

# 3. Improve summarize_text to ensure summaries differ from titles
def summarize_text(text, company_name=None, title_text=""):
    """
    Create an insightful summary of news article text that avoids redundancy with the title.
    
    Args:
        text (str): The article text to summarize
        company_name (str, optional): The company name for context
        title_text (str): The title text to avoid redundancy
    
    Returns:
        str: An insightful summary
    """
    # Handle empty text
    if not text or len(text) < 20:
        return "No article content available to summarize."
    
    # Clean the article text
    text = clean_article_text(text)
    
    # Extract title words for comparison later
    title_words = set(re.findall(r'\b\w+\b', title_text.lower())) if title_text else set()
    
    # First try with transformers if available (most sophisticated)
    if TRANSFORMERS_AVAILABLE:
        transformer_summary = summarize_with_transformers(text, company_name, title_text)
        if transformer_summary:
            # Extra check to ensure transformer summary differs from title
            summary_words = set(re.findall(r'\b\w+\b', transformer_summary.lower()))
            # Calculate word overlap
            if title_words:
                overlap = len(summary_words.intersection(title_words)) / max(len(title_words), 1)
                if overlap < 0.7:  # Less than 70% overlap is acceptable
                    return transformer_summary
            else:
                return transformer_summary
    
    # Otherwise, use extractive summarization approach
    try:
        # Make sure NLTK resources are downloaded
        ensure_nltk_resources()
        
        # Extract keywords
        keywords = extract_keywords(text)
        
        # Extract important sentences (passing title to avoid redundancy)
        important_sentences = extract_important_sentences(text, keywords, title_text=title_text)
        
        # NEW: Ensure we don't start the summary with the title or a very similar sentence
        if important_sentences and title_text:
            first_sentence = important_sentences[0].lower()
            title_lower = title_text.lower()
            
            # Check similarity between first sentence and title
            if first_sentence == title_lower or (
                    len(first_sentence) > 0 and len(title_lower) > 0 and
                    (first_sentence in title_lower or title_lower in first_sentence)):
                # Remove first sentence if it's too similar to title
                if len(important_sentences) > 1:
                    important_sentences = important_sentences[1:]
                # If we only have one sentence, try to get more sentences
                else:
                    # Try to extract different sentences
                    more_sentences = extract_important_sentences(text, keywords, max_sentences=5, title_text=title_text)
                    for sentence in more_sentences:
                        if sentence.lower() != title_lower and title_lower not in sentence.lower():
                            important_sentences = [sentence]
                            break
        
        # Format into coherent summary (without "Regarding" prefix)
        summary = format_summary(important_sentences)
        
        # Final cleanup and quality check
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        # If summary is too short or appears incomplete, try to expand it
        if len(summary) < 100 and len(text) > 500:
            # Try to extract more sentences
            more_sentences = extract_important_sentences(text, keywords, max_sentences=6, title_text=title_text)
            summary = format_summary(more_sentences)
        
        # Final check for trailing ellipses (we want complete sentences)
        if summary.endswith('...'):
            # Try to find a complete sentence ending
            last_period = summary[:-3].rfind('.')
            if last_period > len(summary) * 0.7:  # If we can keep most of the summary
                summary = summary[:last_period+1]
            else:
                # Try to complete the last sentence if possible
                partial_last_sentence = summary[summary.rfind('. ')+2:-3]
                if partial_last_sentence:
                    # Look for the complete sentence in the original text
                    sentence_start = text.find(partial_last_sentence)
                    if sentence_start >= 0:
                        # Find the end of this sentence in the original text
                        sentence_end = text.find('.', sentence_start + len(partial_last_sentence))
                        if sentence_end > 0:
                            last_full_sentence = text[sentence_start:sentence_end+1]
                            # Replace partial sentence with complete one
                            summary = summary[:summary.rfind('. ')+2] + last_full_sentence
        
        # NEW: Final check to ensure summary differs significantly from title
        if summary and title_text:
            summary_words = set(re.findall(r'\b\w+\b', summary.lower()))
            if title_words:
                overlap = len(summary_words.intersection(title_words)) / max(len(title_words), 1)
                
                # If overlap is too high (>70%), try to find different sentences
                if overlap > 0.7 and len(text) > 200:
                    # Get more diverse sentences by excluding first few sentences
                    sentences = sent_tokenize(text)
                    if len(sentences) > 5:
                        alt_text = ' '.join(sentences[2:])  # Skip first two sentences
                        alt_keywords = extract_keywords(alt_text)
                        alt_sentences = extract_important_sentences(alt_text, alt_keywords, max_sentences=4)
                        alt_summary = format_summary(alt_sentences)
                        
                        # Use alternative summary if it's substantial enough
                        if len(alt_summary) > 100:
                            return alt_summary
        
        return summary
    except Exception as e:
        print(f"Error during summarization: {e}")
        
        # Fallback to simple summary if errors occur
        try:
            sentences = simple_sentence_tokenize(text)
            if sentences and len(sentences) > 0:
                if len(sentences) >= 3:
                    return sentences[0] + " " + sentences[1] + " " + sentences[2]
                return ' '.join(sentences[:2])
        except:
            pass
        
        # Ultimate fallback - extract first paragraph
        paragraphs = re.split(r'\n\s*\n', text)
        if paragraphs and len(paragraphs[0]) > 30:
            return paragraphs[0]
        
        return text[:250].strip() + " [Truncated due to processing error]"