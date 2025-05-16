import os
import re
import argparse
import json
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
from datetime import datetime

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("Downloading required NLTK data...")
    nltk.download('punkt')
    nltk.download('vader_lexicon')
    nltk.download('punkt_tab')

nltk.download('punkt_tab')
class AIConversationAnalyzer:
    def __init__(self, output_dir="ai_conversation_analysis"):
        """
        Initialize the AI conversation analyzer.
        
        Args:
            output_dir: Directory to save analysis reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize tools
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Patterns for detecting different features in conversations
        self.patterns = {
            'code_block': r'```[\s\S]*?```',  # Code blocks in markdown
            'url': r'https?://\S+',  # URLs
            'bullet_points': r'^\s*[-*•]\s',  # Bullet points
            'numbered_list': r'^\s*\d+\.\s',  # Numbered lists
            'question': r'\?\s*$',  # Questions
        }
        
        # Technical keywords that indicate sophistication
        self.tech_keywords = [
            'algorithm', 'optimize', 'refactor', 'architecture', 'design pattern',
            'efficiency', 'complexity', 'performance', 'scalability', 'security',
            'implementation', 'interface', 'encapsulation', 'inheritance', 'polymorphism',
            'abstraction', 'asynchronous', 'concurrency', 'parallelism', 'robust',
            'maintainable', 'testable', 'modular', 'dependency', 'framework'
        ]
        
        # Problem-solving approach keywords
        self.problem_solving_keywords = [
            'analyze', 'consider', 'alternative', 'approach', 'strategy',
            'solution', 'implement', 'evaluate', 'improve', 'optimize',
            'enhance', 'test', 'debug', 'fix', 'resolve', 'issue',
            'problem', 'challenge', 'requirement', 'specification', 'constraint',
            'trade-off', 'balance', 'compare', 'contrast', 'decide'
        ]
        
        # Reflective and critical thinking keywords
        self.critical_thinking_keywords = [
            'however', 'although', 'nevertheless', 'alternatively', 'consider',
            'evaluate', 'analyze', 'critique', 'assess', 'review',
            'limitation', 'drawback', 'advantage', 'disadvantage', 'trade-off',
            'better', 'worse', 'improve', 'enhancement', 'modification',
            'suggestion', 'recommendation', 'instead', 'rather', 'preferable'
        ]
        
        # Prompt engineering keywords
        self.prompt_engineering_keywords = [
            'specific', 'detail', 'example', 'context', 'clarify',
            'refine', 'prompt', 'instruction', 'request', 'query',
            'input', 'format', 'structure', 'constraint', 'condition',
            'output', 'expect', 'generate', 'produce', 'create',
            'step-by-step', 'systematic', 'approach', 'method', 'technique'
        ]
    
    def parse_conversation(self, file_path):
        """
        Parse a conversation from a text file.
        
        Args:
            file_path: Path to the text file containing the conversation
            
        Returns:
            List of message dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to determine the format based on content
            messages = []
            
            # Look for patterns like [USER] or [ASSISTANT]
            role_pattern = r'\[(USER|ASSISTANT|HUMAN|AI|GPT|CLAUDE)\]\s*\n(.*?)(?=\n\s*\[|\Z)'
            role_matches = re.findall(role_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if role_matches:
                # Format with [ROLE] markers
                for role, text in role_matches:
                    normalized_role = 'user' if role.upper() in ['USER', 'HUMAN'] else 'assistant'
                    messages.append({
                        'role': normalized_role,
                        'content': text.strip()
                    })
            else:
                # Try to detect JSON format (common in API outputs)
                try:
                    json_data = json.loads(content)
                    if isinstance(json_data, list) and all('role' in item and 'content' in item for item in json_data):
                        messages = json_data
                    elif 'messages' in json_data and isinstance(json_data['messages'], list):
                        messages = json_data['messages']
                except json.JSONDecodeError:
                    # Not JSON format, try other patterns
                    
                    # Try to detect patterns like "User:" or "Assistant:"
                    role_pattern2 = r'(User|Human|Assistant|AI|Claude|GPT):\s*(.*?)(?=\n\s*(?:User|Human|Assistant|AI|Claude|GPT):|$)'
                    role_matches2 = re.findall(role_pattern2, content, re.DOTALL | re.IGNORECASE)
                    
                    if role_matches2:
                        for role, text in role_matches2:
                            normalized_role = 'user' if role.lower() in ['user', 'human'] else 'assistant'
                            messages.append({
                                'role': normalized_role,
                                'content': text.strip()
                            })
                    else:
                        # Try to detect alternating patterns without explicit markers
                        paragraphs = re.split(r'\n\s*\n', content)
                        
                        # Assume first message is from user, then alternating
                        for i, paragraph in enumerate(paragraphs):
                            if paragraph.strip():
                                role = 'user' if i % 2 == 0 else 'assistant'
                                messages.append({
                                    'role': role,
                                    'content': paragraph.strip()
                                })
            
            return messages
        
        except Exception as e:
            print(f"Error parsing conversation {file_path}: {e}")
            return []
    
    def analyze_conversation(self, messages):
        """
        Analyze a conversation for various metrics.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        if not messages:
            return {
                'error': 'No messages found in conversation',
                'metrics': {}
            }
        
        # Extract user and assistant messages
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        # Calculate exchange count (number of user-assistant pairs)
        exchange_count = min(len(user_messages), len(assistant_messages))
        
        # Calculate message counts and average lengths
        user_msg_count = len(user_messages)
        assistant_msg_count = len(assistant_messages)
        
        user_avg_length = sum(len(msg['content']) for msg in user_messages) / max(1, user_msg_count)
        assistant_avg_length = sum(len(msg['content']) for msg in assistant_messages) / max(1, assistant_msg_count)
        
        # Analyze user prompts
        user_prompt_scores = [self._analyze_prompt(msg['content']) for msg in user_messages]
        
        # Analyze assistant responses
        assistant_response_scores = [self._analyze_response(msg['content']) for msg in assistant_messages]
        
        # Analyze user-assistant exchanges for improvements and critical evaluation
        exchange_analyses = []
        
        for i in range(min(len(user_messages), len(assistant_messages))):
            user_msg = user_messages[i]['content']
            assistant_msg = assistant_messages[i]['content']
            
            # In subsequent exchanges, the user might evaluate the previous response
            if i > 0:
                prev_assistant_msg = assistant_messages[i-1]['content']
                exchange_analyses.append(self._analyze_exchange(user_msg, assistant_msg, prev_assistant_msg))
            else:
                exchange_analyses.append(self._analyze_exchange(user_msg, assistant_msg))
        
        # Analyze prompt progression over time
        prompt_progression = self._analyze_prompt_progression(user_messages)
        
        # Analyze critical evaluation
        critical_evaluation = self._analyze_critical_evaluation(user_messages, assistant_messages)
        
        # Analyze implementation improvements
        implementation_improvements = self._analyze_implementation_improvements(user_messages, assistant_messages)
        
        # Aggregate metrics
        metrics = {
            'exchange_count': exchange_count,
            'user_message_count': user_msg_count,
            'assistant_message_count': assistant_msg_count,
            'user_avg_message_length': user_avg_length,
            'assistant_avg_message_length': assistant_avg_length,
            'user_prompt_scores': user_prompt_scores,
            'assistant_response_scores': assistant_response_scores,
            'exchange_analyses': exchange_analyses,
            'prompt_progression': prompt_progression,
            'critical_evaluation': critical_evaluation,
            'implementation_improvements': implementation_improvements
        }
        
        # Calculate rubric scores
        rubric_scores = self._calculate_rubric_scores(metrics)
        
        return {
            'metrics': metrics,
            'rubric_scores': rubric_scores
        }
    
    def _analyze_prompt(self, text):
        """
        Analyze a user prompt for quality and sophistication.
        
        Args:
            text: The prompt text
            
        Returns:
            Score dictionary
        """
        # Calculate basic metrics
        word_count = len(text.split())
        sentence_count = len(sent_tokenize(text))
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # Check for specific features
        has_code_block = bool(re.search(self.patterns['code_block'], text))
        has_bullet_points = bool(re.search(self.patterns['bullet_points'], text, re.MULTILINE))
        has_numbered_list = bool(re.search(self.patterns['numbered_list'], text, re.MULTILINE))
        has_question = bool(re.search(self.patterns['question'], text, re.MULTILINE))
        
        # Count keywords
        tech_keyword_count = sum(1 for keyword in self.tech_keywords if keyword.lower() in text.lower())
        problem_solving_count = sum(1 for keyword in self.problem_solving_keywords if keyword.lower() in text.lower())
        prompt_engineering_count = sum(1 for keyword in self.prompt_engineering_keywords if keyword.lower() in text.lower())
        
        # Count specific instructions or constraints
        specific_instruction_count = len(re.findall(r'(please|can you|could you|would you)[^.?!]*', text, re.IGNORECASE))
        
        # Calculate prompt specificity score
        specificity_score = min(10, (word_count / 20) + 
                             (has_code_block * 2) + 
                             (has_bullet_points * 1) + 
                             (has_numbered_list * 1) + 
                             (tech_keyword_count * 0.5) + 
                             (specific_instruction_count * 0.5))
        
        # Calculate prompt sophistication score
        sophistication_score = min(10, (tech_keyword_count * 0.7) + 
                                (problem_solving_count * 0.5) + 
                                (prompt_engineering_count * 0.8) + 
                                (has_code_block * 1) + 
                                (avg_sentence_length / 5))
        
        # Overall prompt quality score
        overall_score = (specificity_score * 0.6) + (sophistication_score * 0.4)
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
            'has_code_block': has_code_block,
            'has_bullet_points': has_bullet_points,
            'has_numbered_list': has_numbered_list,
            'has_question': has_question,
            'tech_keyword_count': tech_keyword_count,
            'problem_solving_count': problem_solving_count,
            'prompt_engineering_count': prompt_engineering_count,
            'specific_instruction_count': specific_instruction_count,
            'specificity_score': specificity_score,
            'sophistication_score': sophistication_score,
            'overall_score': overall_score
        }
    
    def _analyze_response(self, text):
        """
        Analyze an assistant response for quality and sophistication.
        
        Args:
            text: The response text
            
        Returns:
            Score dictionary
        """
        # Calculate basic metrics
        word_count = len(text.split())
        sentence_count = len(sent_tokenize(text))
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # Check for specific features
        has_code_block = bool(re.search(self.patterns['code_block'], text))
        has_bullet_points = bool(re.search(self.patterns['bullet_points'], text, re.MULTILINE))
        has_numbered_list = bool(re.search(self.patterns['numbered_list'], text, re.MULTILINE))
        
        # Extract code blocks for further analysis
        code_blocks = re.findall(self.patterns['code_block'], text)
        code_block_count = len(code_blocks)
        code_lines = sum(block.count('\n') for block in code_blocks)
        
        # Count explanatory words/phrases
        explanation_phrases = ['because', 'since', 'as a result', 'therefore', 'consequently', 
                            'this means', 'in other words', 'to clarify', 'for example', 
                            'for instance', 'such as', 'to illustrate']
        explanation_count = sum(1 for phrase in explanation_phrases if phrase.lower() in text.lower())
        
        # Count technical terms
        tech_keyword_count = sum(1 for keyword in self.tech_keywords if keyword.lower() in text.lower())
        
        # Count alternatives/options presented
        alternatives_count = sum(1 for phrase in ['alternatively', 'another option', 'another approach', 
                                                'you could also', 'another way'] 
                                if phrase.lower() in text.lower())
        
        # Calculate response quality score
        quality_score = min(10, (word_count / 50) + 
                           (code_block_count * 2) + 
                           (explanation_count * 0.7) + 
                           (tech_keyword_count * 0.3) + 
                           (alternatives_count * 0.8))
        
        # Calculate response depth score
        depth_score = min(10, (code_lines / 5) + 
                        (explanation_count * 0.8) + 
                        (tech_keyword_count * 0.5) + 
                        (has_bullet_points * 1) + 
                        (has_numbered_list * 1))
        
        # Overall response quality score
        overall_score = (quality_score * 0.5) + (depth_score * 0.5)
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
            'has_code_block': has_code_block,
            'code_block_count': code_block_count,
            'code_lines': code_lines,
            'has_bullet_points': has_bullet_points,
            'has_numbered_list': has_numbered_list,
            'explanation_count': explanation_count,
            'tech_keyword_count': tech_keyword_count,
            'alternatives_count': alternatives_count,
            'quality_score': quality_score,
            'depth_score': depth_score,
            'overall_score': overall_score
        }
    
    def _analyze_exchange(self, user_msg, assistant_msg, prev_assistant_msg=None):
        """
        Analyze a user-assistant exchange for improvement and critical evaluation.
        
        Args:
            user_msg: User message text
            assistant_msg: Assistant message text
            prev_assistant_msg: Previous assistant message (if any)
            
        Returns:
            Exchange analysis dictionary
        """
        # Check if user message contains critical evaluation
        critical_terms = ['improve', 'better', 'instead', 'issue', 'problem', 'error', 'bug', 
                        'incorrect', 'wrong', 'fix', 'update', 'change', 'modify', 'revise']
        
        has_critical_evaluation = any(term.lower() in user_msg.lower() for term in critical_terms)
        critical_eval_count = sum(1 for term in critical_terms if term.lower() in user_msg.lower())
        
        # Check for specific critical feedback in user message
        specific_feedback = 0
        if prev_assistant_msg:
            # Look for references to specific parts of the previous message
            code_references = len(re.findall(r'(line|function|method|class|variable|parameter|argument|return|value|code|snippet)', 
                                         user_msg, re.IGNORECASE))
            specific_feedback = code_references
        
        # Check for improvement suggestions
        suggestion_phrases = ['you could', 'try to', 'could be', 'should be', 'better to', 
                           'instead of', 'rather than', 'consider', 'maybe', 'perhaps']
        
        suggestion_count = sum(1 for phrase in suggestion_phrases if phrase.lower() in user_msg.lower())
        
        # Calculate critical evaluation score
        critical_score = min(10, (critical_eval_count * 1.5) + 
                          (specific_feedback * 2) + 
                          (suggestion_count * 1.2) + 
                          (has_critical_evaluation * 2))
        
        # Check for implementation details in assistant response
        implementation_details = len(re.findall(r'(implement|code|function|class|method|algorithm|structure|pattern|design|architecture)', 
                                           assistant_msg, re.IGNORECASE))
        
        # Check for explanations of changes/improvements
        explanation_phrases = ['improved by', 'changed to', 'modified to', 'updated to', 
                             'fixed by', 'replaced with', 'refactored to', 'optimized by']
        
        explanation_count = sum(1 for phrase in explanation_phrases if phrase.lower() in assistant_msg.lower())
        
        # Calculate implementation improvement score
        implementation_score = min(10, (implementation_details * 0.8) + 
                                (explanation_count * 1.5))
        
        return {
            'has_critical_evaluation': has_critical_evaluation,
            'critical_eval_count': critical_eval_count,
            'specific_feedback': specific_feedback,
            'suggestion_count': suggestion_count,
            'critical_score': critical_score,
            'implementation_details': implementation_details,
            'explanation_count': explanation_count,
            'implementation_score': implementation_score
        }
    
    def _analyze_prompt_progression(self, user_messages):
        """
        Analyze how user prompts evolve over the conversation.
        
        Args:
            user_messages: List of user message dictionaries
            
        Returns:
            Prompt progression analysis dictionary
        """
        if len(user_messages) < 2:
            return {
                'has_progression': False,
                'progression_score': 0,
                'prompt_scores': []
            }
        
        # Calculate scores for each prompt
        prompt_scores = [self._analyze_prompt(msg['content'])['overall_score'] for msg in user_messages]
        
        # Calculate the trend (are later prompts better?)
        score_diffs = [prompt_scores[i] - prompt_scores[i-1] for i in range(1, len(prompt_scores))]
        avg_diff = sum(score_diffs) / len(score_diffs)
        
        # Calculate correlation with message position
        positions = list(range(1, len(prompt_scores) + 1))
        correlation = np.corrcoef(positions, prompt_scores)[0, 1] if len(prompt_scores) > 2 else avg_diff
        
        # Check if prompts get more specific/detailed over time
        word_counts = [len(msg['content'].split()) for msg in user_messages]
        keyword_counts = [sum(1 for keyword in self.prompt_engineering_keywords 
                         if keyword.lower() in msg['content'].lower()) 
                         for msg in user_messages]
        
        # Calculate progression metrics
        specificity_progression = sum(word_counts[i] - word_counts[i-1] for i in range(1, len(word_counts))) / max(1, len(word_counts) - 1)
        keyword_progression = sum(keyword_counts[i] - keyword_counts[i-1] for i in range(1, len(keyword_counts))) / max(1, len(keyword_counts) - 1)
        
        # Calculate overall progression score
        progression_score = min(10, (correlation * 5) + 
                              (avg_diff * 3) + 
                              (specificity_progression / 20) + 
                              (keyword_progression * 2))
        
        if progression_score < 0:
            progression_score = 0
        
        return {
            'has_progression': progression_score > 3,
            'progression_score': progression_score,
            'prompt_scores': prompt_scores,
            'score_trend': avg_diff,
            'correlation': correlation,
            'specificity_progression': specificity_progression,
            'keyword_progression': keyword_progression
        }
    
    def _analyze_critical_evaluation(self, user_messages, assistant_messages):
        """
        Analyze critical evaluation of AI output throughout the conversation.
        
        Args:
            user_messages: List of user message dictionaries
            assistant_messages: List of assistant message dictionaries
            
        Returns:
            Critical evaluation analysis dictionary
        """
        if len(user_messages) < 2 or len(assistant_messages) < 1:
            return {
                'has_critical_evaluation': False,
                'critical_eval_score': 0,
                'evaluation_depth': 0
            }
        
        # Look for critical evaluation in user messages after the first message
        critical_terms = ['improve', 'better', 'instead', 'issue', 'problem', 'error', 'bug', 
                        'incorrect', 'wrong', 'fix', 'update', 'change', 'modify', 'revise',
                        'limitation', 'drawback', 'concern', 'question', 'clarify']
        
        # Count critical terms in each message
        critical_counts = [sum(1 for term in critical_terms if term.lower() in msg['content'].lower()) 
                         for msg in user_messages[1:]]  # Skip first message
        
        # Count critical thinking keywords
        critical_thinking_counts = [sum(1 for keyword in self.critical_thinking_keywords 
                                  if keyword.lower() in msg['content'].lower()) 
                                  for msg in user_messages[1:]]  # Skip first message
        
        # Check for references to code or specific parts of assistant responses
        code_reference_counts = [len(re.findall(r'(line|function|method|class|variable|parameter|argument|return|value|code|snippet)', 
                                           msg['content'], re.IGNORECASE)) 
                               for msg in user_messages[1:]]  # Skip first message
        
        # Check for specific quotes or references to assistant's output
        quote_reference_counts = [len(re.findall(r'"([^"]*)"', msg['content'])) for msg in user_messages[1:]]
        
        # Calculate evaluation depth
        evaluation_depth = sum(critical_counts) / max(1, len(critical_counts))
        thinking_depth = sum(critical_thinking_counts) / max(1, len(critical_thinking_counts))
        reference_depth = (sum(code_reference_counts) + sum(quote_reference_counts)) / max(1, len(code_reference_counts))
        
        # Calculate overall critical evaluation score
        critical_eval_score = min(10, (evaluation_depth * 1.5) + 
                                (thinking_depth * 2) + 
                                (reference_depth * 1.5))
        
        return {
            'has_critical_evaluation': critical_eval_score > 3,
            'critical_eval_score': critical_eval_score,
            'evaluation_depth': evaluation_depth,
            'thinking_depth': thinking_depth,
            'reference_depth': reference_depth,
            'critical_counts': critical_counts,
            'critical_thinking_counts': critical_thinking_counts,
            'code_reference_counts': code_reference_counts,
            'quote_reference_counts': quote_reference_counts
        }
    
    def _analyze_implementation_improvements(self, user_messages, assistant_messages):
        """
        Analyze implementation improvements beyond AI suggestions.
        
        Args:
            user_messages: List of user message dictionaries
            assistant_messages: List of assistant message dictionaries
            
        Returns:
            Implementation improvements analysis dictionary
        """
        if len(user_messages) < 2 or len(assistant_messages) < 1:
            return {
                'has_implementation_improvements': False,
                'implementation_score': 0,
                'improvement_depth': 0
            }
        
        # Look for implementation-related terms in user messages after the first exchange
        implementation_terms = ['implement', 'modify', 'change', 'improve', 'add', 'update', 
                             'enhance', 'extend', 'refactor', 'optimize', 'fix']
        
        # Count implementation terms in each message
        implementation_counts = [sum(1 for term in implementation_terms if term.lower() in msg['content'].lower()) 
                               for msg in user_messages[1:]]  # Skip first message
        
        # Check for code sharing by user (showing their implementations)
        user_code_blocks = [len(re.findall(self.patterns['code_block'], msg['content'])) 
                          for msg in user_messages[1:]]  # Skip first message
        
        # Check for specific improvements mentioned
        improvement_phrases = ['I changed', 'I modified', 'I added', 'I implemented', 'I updated', 
                            'I improved', 'I extended', 'I refactored', 'I fixed', 'I created']
        
        improvement_counts = [sum(1 for phrase in improvement_phrases 
                                if phrase.lower() in msg['content'].lower()) 
                              for msg in user_messages[1:]]  # Skip first message
        
        # Calculate improvement metrics
        implementation_depth = sum(implementation_counts) / max(1, len(implementation_counts))
        code_sharing_depth = sum(user_code_blocks) / max(1, len(user_code_blocks))
        improvement_specificity = sum(improvement_counts) / max(1, len(improvement_counts))
        
        # Calculate overall implementation improvement score
        implementation_score = min(10, (implementation_depth * 1.2) + 
                                 (code_sharing_depth * 3) + 
                                 (improvement_specificity * 2))
        
        return {
            'has_implementation_improvements': implementation_score > 3,
            'implementation_score': implementation_score,
            'improvement_depth': implementation_depth,
            'code_sharing_depth': code_sharing_depth,
            'improvement_specificity': improvement_specificity,
            'implementation_counts': implementation_counts,
            'user_code_blocks': user_code_blocks,
            'improvement_counts': improvement_counts
        }
    
    def _calculate_rubric_scores(self, metrics):
        """
        Calculate scores according to the rubric categories.
        
        Args:
            metrics: Dictionary with conversation metrics
            
        Returns:
            Dictionary with rubric scores
        """
        # 1. Depth and relevance of AI interactions (5%)
        exchange_count = metrics['exchange_count']
        avg_response_score = sum(score['overall_score'] for score in metrics['assistant_response_scores']) / max(1, len(metrics['assistant_response_scores']))
        
        # Scale from 0-10 to 0-5 points according to the rubric
        if exchange_count >= 5 and avg_response_score >= 7.5:
            ai_interaction_level = "Distinction (75-100%)"
            ai_interaction_percentage = min(100, 75 + (avg_response_score - 7.5) * 5)
            ai_interaction_points = 5 * ai_interaction_percentage / 100
        elif exchange_count >= 4 and avg_response_score >= 6:
            ai_interaction_level = "Credit (65-74%)"
            ai_interaction_percentage = 65 + (min(exchange_count, 5) - 4) * 9
            ai_interaction_points = 5 * ai_interaction_percentage / 100
        elif exchange_count >= 3 and avg_response_score >= 5:
            ai_interaction_level = "Pass (50-64%)"
            ai_interaction_percentage = 50 + (min(exchange_count, 4) - 3) * 14
            ai_interaction_points = 5 * ai_interaction_percentage / 100
        else:
            ai_interaction_level = "Fail (0-49%)"
            ai_interaction_percentage = min(49, (exchange_count / 3) * 49)
            ai_interaction_points = 5 * ai_interaction_percentage / 100
        
        # 2. Prompt engineering evolution (5%)
        progression = metrics['prompt_progression']
        progression_score = progression['progression_score']
        
        if progression_score >= 7.5:
            prompt_evolution_level = "Distinction (75-100%)"
            prompt_evolution_percentage = min(100, 75 + (progression_score - 7.5) * 5)
            prompt_evolution_points = 5 * prompt_evolution_percentage / 100
        elif progression_score >= 6:
            prompt_evolution_level = "Credit (65-74%)"
            prompt_evolution_percentage = 65 + (progression_score - 6) * 9 / 1.5
            prompt_evolution_points = 5 * prompt_evolution_percentage / 100
        elif progression_score >= 4:
            prompt_evolution_level = "Pass (50-64%)"
            prompt_evolution_percentage = 50 + (progression_score - 4) * 14 / 2
            prompt_evolution_points = 5 * prompt_evolution_percentage / 100
        else:
            prompt_evolution_level = "Fail (0-49%)"
            prompt_evolution_percentage = min(49, (progression_score / 4) * 49)
            prompt_evolution_points = 5 * prompt_evolution_percentage / 100
        
        # 3. Critical evaluation of AI-generated output (5%)
        critical_eval = metrics['critical_evaluation']
        critical_eval_score = critical_eval['critical_eval_score']
        
        if critical_eval_score >= 7.5:
            critical_eval_level = "Distinction (75-100%)"
            critical_eval_percentage = min(100, 75 + (critical_eval_score - 7.5) * 5)
            critical_eval_points = 5 * critical_eval_percentage / 100
        elif critical_eval_score >= 6:
            critical_eval_level = "Credit (65-74%)"
            critical_eval_percentage = 65 + (critical_eval_score - 6) * 9 / 1.5
            critical_eval_points = 5 * critical_eval_percentage / 100
        elif critical_eval_score >= 4:
            critical_eval_level = "Pass (50-64%)"
            critical_eval_percentage = 50 + (critical_eval_score - 4) * 14 / 2
            critical_eval_points = 5 * critical_eval_percentage / 100
        else:
            critical_eval_level = "Fail (0-49%)"
            critical_eval_percentage = min(49, (critical_eval_score / 4) * 49)
            critical_eval_points = 5 * critical_eval_percentage / 100
        
        # 4. Implementation improvements beyond AI suggestions (5%)
        impl_improvements = metrics['implementation_improvements']
        impl_score = impl_improvements['implementation_score']
        
        if impl_score >= 7.5:
            impl_level = "Distinction (75-100%)"
            impl_percentage = min(100, 75 + (impl_score - 7.5) * 5)
            impl_points = 5 * impl_percentage / 100
        elif impl_score >= 6:
            impl_level = "Credit (65-74%)"
            impl_percentage = 65 + (impl_score - 6) * 9 / 1.5
            impl_points = 5 * impl_percentage / 100
        elif impl_score >= 4:
            impl_level = "Pass (50-64%)"
            impl_percentage = 50 + (impl_score - 4) * 14 / 2
            impl_points = 5 * impl_percentage / 100
        else:
            impl_level = "Fail (0-49%)"
            impl_percentage = min(49, (impl_score / 4) * 49)
            impl_points = 5 * impl_percentage / 100
        
        # Total AI Integration & Critical Interaction (20%)
        total_points = ai_interaction_points + prompt_evolution_points + critical_eval_points + impl_points
        total_percentage = total_points * 5  # 20% total weight divided by 4 categories
        
        return {
            'ai_interactions': {
                'level': ai_interaction_level,
                'percentage': ai_interaction_percentage,
                'points': ai_interaction_points,
                'max_points': 5
            },
            'prompt_engineering': {
                'level': prompt_evolution_level,
                'percentage': prompt_evolution_percentage,
                'points': prompt_evolution_points,
                'max_points': 5
            },
            'critical_evaluation': {
                'level': critical_eval_level,
                'percentage': critical_eval_percentage,
                'points': critical_eval_points,
                'max_points': 5
            },
            'implementation_improvements': {
                'level': impl_level,
                'percentage': impl_percentage,
                'points': impl_points,
                'max_points': 5
            },
            'total': {
                'points': total_points,
                'percentage': total_percentage,
                'max_points': 20
            }
        }
    
    def analyze_conversation_file(self, file_path):
        """
        Analyze a conversation file and generate a report.
        
        Args:
            file_path: Path to the conversation text file
            
        Returns:
            Dictionary with analysis results
        """
        # Parse the conversation
        messages = self.parse_conversation(file_path)
        
        if not messages:
            print(f"No messages found in {file_path}")
            return None
        
        # Analyze the conversation
        analysis = self.analyze_conversation(messages)
        
        # Add file metadata
        analysis['file_path'] = file_path
        analysis['file_name'] = os.path.basename(file_path)
        
        return analysis
    
    def generate_report(self, analysis, output_file=None):
        """
        Generate a Markdown report for a conversation analysis.
        
        Args:
            analysis: Dictionary with conversation analysis
            output_file: Path to save the report (optional)
            
        Returns:
            Report text
        """
        if not analysis:
            return "No analysis data provided."
        
        file_name = analysis.get('file_name', 'Unknown')
        
        report = f"# AI Conversation Analysis: {file_name}\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Summary of key metrics
        metrics = analysis.get('metrics', {})
        exchange_count = metrics.get('exchange_count', 0)
        
        report += "## Summary\n\n"
        report += f"- **Conversation Exchanges:** {exchange_count}\n"
        report += f"- **User Messages:** {metrics.get('user_message_count', 0)}\n"
        report += f"- **Assistant Messages:** {metrics.get('assistant_message_count', 0)}\n\n"
        
        # Rubric scores
        rubric_scores = analysis.get('rubric_scores', {})
        
        report += "## Rubric Assessment\n\n"
        
        # AI Interactions
        ai_interactions = rubric_scores.get('ai_interactions', {})
        report += "### Depth and relevance of AI interactions (5%)\n\n"
        report += f"**Performance Level:** {ai_interactions.get('level', 'Not assessed')}\n\n"
        report += f"**Score:** {ai_interactions.get('points', 0):.2f}/{ai_interactions.get('max_points', 5)} ({ai_interactions.get('percentage', 0):.1f}%)\n\n"
        report += "| Performance Level | Description | Points |\n"
        report += "|-------------------|-------------|--------|\n"
        report += "| Distinction (75-100%) | 5+ sophisticated AI exchanges demonstrating expert problem-solving approach | 3.75-5 |\n"
        report += "| Credit (65-74%) | 4-5 AI exchanges showing good problem-solving strategy | 3.25-3.74 |\n"
        report += "| Pass (50-64%) | Minimum 3 AI exchanges with basic problem-solving | 2.5-3.24 |\n"
        report += "| Fail (0-49%) | Fewer than 3 exchanges or exchanges lacking relevance | 0-2.49 |\n\n"
        
        # Prompt Engineering
        prompt_engineering = rubric_scores.get('prompt_engineering', {})
        report += "### Prompt engineering evolution (5%)\n\n"
        report += f"**Performance Level:** {prompt_engineering.get('level', 'Not assessed')}\n\n"
        report += f"**Score:** {prompt_engineering.get('points', 0):.2f}/{prompt_engineering.get('max_points', 5)} ({prompt_engineering.get('percentage', 0):.1f}%)\n\n"
        report += "| Performance Level | Description | Points |\n"
        report += "|-------------------|-------------|--------|\n"
        report += "| Distinction (75-100%) | Sophisticated prompt engineering showing expert understanding of AI capabilities | 3.75-5 |\n"
        report += "| Credit (65-74%) | Clear progression in prompt quality and effectiveness | 3.25-3.74 |\n"
        report += "| Pass (50-64%) | Shows basic refinement of prompts | 2.5-3.24 |\n"
        report += "| Fail (0-49%) | Little or no progression in prompt quality | 0-2.49 |\n\n"
        
        # Critical Evaluation
        critical_evaluation = rubric_scores.get('critical_evaluation', {})
        report += "### Critical evaluation of AI-generated output (5%)\n\n"
        report += f"**Performance Level:** {critical_evaluation.get('level', 'Not assessed')}\n\n"
        report += f"**Score:** {critical_evaluation.get('points', 0):.2f}/{critical_evaluation.get('max_points', 5)} ({critical_evaluation.get('percentage', 0):.1f}%)\n\n"
        report += "| Performance Level | Description | Points |\n"
        report += "|-------------------|-------------|--------|\n"
        report += "| Distinction (75-100%) | Comprehensive evaluation demonstrating expert-level technical understanding | 3.75-5 |\n"
        report += "| Credit (65-74%) | Thorough evaluation showing good understanding of code quality | 3.25-3.74 |\n"
        report += "| Pass (50-64%) | Basic evaluation identifying obvious issues | 2.5-3.24 |\n"
        report += "| Fail (0-49%) | Minimal or superficial evaluation of AI output | 0-2.49 |\n\n"
        
        # Implementation Improvements
        implementation_improvements = rubric_scores.get('implementation_improvements', {})
        report += "### Implementation improvements beyond AI suggestions (5%)\n\n"
        report += f"**Performance Level:** {implementation_improvements.get('level', 'Not assessed')}\n\n"
        report += f"**Score:** {implementation_improvements.get('points', 0):.2f}/{implementation_improvements.get('max_points', 5)} ({implementation_improvements.get('percentage', 0):.1f}%)\n\n"
        report += "| Performance Level | Description | Points |\n"
        report += "|-------------------|-------------|--------|\n"
        report += "| Distinction (75-100%) | Substantial improvements demonstrating expertise beyond what AI provided | 3.75-5 |\n"
        report += "| Credit (65-74%) | Significant enhancements showing good technical understanding | 3.25-3.74 |\n"
        report += "| Pass (50-64%) | Basic improvements to AI code | 2.5-3.24 |\n"
        report += "| Fail (0-49%) | Minimal or no improvements beyond AI suggestions | 0-2.49 |\n\n"
        
        # Total Score
        total = rubric_scores.get('total', {})
        report += "### Total AI Integration & Critical Interaction Score (20%)\n\n"
        report += f"**Total Points:** {total.get('points', 0):.2f}/{total.get('max_points', 20)} ({total.get('percentage', 0):.1f}%)\n\n"
        
        # Detailed Analysis
        report += "## Detailed Analysis\n\n"
        
        # Exchange analysis
        report += "### Conversation Exchanges\n\n"
        
        # Generate exchange quality metrics
        user_prompt_scores = metrics.get('user_prompt_scores', [])
        assistant_response_scores = metrics.get('assistant_response_scores', [])
        
        if user_prompt_scores and assistant_response_scores:
            report += "| Exchange | User Prompt Quality | Assistant Response Quality | Topic |\n"
            report += "|----------|---------------------|----------------------------|-------|\n"
            
            for i in range(min(len(user_prompt_scores), len(assistant_response_scores))):
                # Simplified estimation of topic based on technical keywords
                topic = "Technical" if user_prompt_scores[i].get('tech_keyword_count', 0) > 3 else "General"
                
                report += f"| {i+1} | {user_prompt_scores[i].get('overall_score', 0):.2f}/10 | {assistant_response_scores[i].get('overall_score', 0):.2f}/10 | {topic} |\n"
            
            report += "\n"
        
        # Prompt progression analysis
        prompt_progression = metrics.get('prompt_progression', {})
        
        report += "### Prompt Engineering Evolution\n\n"
        report += f"- **Progression Score:** {prompt_progression.get('progression_score', 0):.2f}/10\n"
        report += f"- **Score Trend:** {prompt_progression.get('score_trend', 0):.2f} (positive values indicate improvement)\n"
        
        # Visualization of prompt scores (ASCII chart)
        prompt_scores = prompt_progression.get('prompt_scores', [])
        if prompt_scores:
            report += "\n**Prompt Quality Progression:**\n\n```\n"
            max_score = max(prompt_scores)
            chart_height = 10
            chart_width = len(prompt_scores)
            
            for h in range(chart_height, 0, -1):
                threshold = max_score * h / chart_height
                line = "  " + "".join("#" if score >= threshold else " " for score in prompt_scores)
                report += line + "\n"
            
            report += "  " + "-" * chart_width + "\n"
            report += "  " + "".join(str(i+1)[0] for i in range(chart_width)) + " (Prompt #)\n"
            report += "```\n\n"
        
        # Critical evaluation analysis
        critical_eval = metrics.get('critical_evaluation', {})
        
        report += "### Critical Evaluation of AI Output\n\n"
        report += f"- **Critical Evaluation Score:** {critical_eval.get('critical_eval_score', 0):.2f}/10\n"
        report += f"- **Evaluation Depth:** {critical_eval.get('evaluation_depth', 0):.2f}\n"
        report += f"- **Technical References:** {critical_eval.get('reference_depth', 0):.2f}\n\n"
        
        # Implementation improvements analysis
        impl_improvements = metrics.get('implementation_improvements', {})
        
        report += "### Implementation Improvements\n\n"
        report += f"- **Implementation Score:** {impl_improvements.get('implementation_score', 0):.2f}/10\n"
        report += f"- **Code Sharing Depth:** {impl_improvements.get('code_sharing_depth', 0):.2f}\n"
        report += f"- **Implementation Specificity:** {impl_improvements.get('improvement_specificity', 0):.2f}\n\n"
        
        # Strengths and recommendations
        report += "## Strengths and Recommendations\n\n"
        
        # Identify strengths based on scores
        report += "### Strengths\n\n"
        strengths = []
        
        if exchange_count >= 5:
            strengths.append("Good number of AI exchanges")
        
        if prompt_progression.get('progression_score', 0) > 6:
            strengths.append("Strong progression in prompt engineering quality")
        
        if critical_eval.get('critical_eval_score', 0) > 6:
            strengths.append("Effective critical evaluation of AI outputs")
        
        if impl_improvements.get('implementation_score', 0) > 6:
            strengths.append("Substantial implementation improvements beyond AI suggestions")
        
        # Check for specific strengths in the metrics
        avg_assistant_score = sum(score.get('overall_score', 0) for score in assistant_response_scores) / max(1, len(assistant_response_scores))
        if avg_assistant_score > 7:
            strengths.append("High quality AI responses indicating effective prompting")
        
        code_blocks_count = sum(score.get('code_block_count', 0) for score in assistant_response_scores)
        if code_blocks_count > 3:
            strengths.append("Good use of code examples in the conversation")
        
        if not strengths:
            strengths.append("Conversation demonstrates engagement with AI")
        
        for strength in strengths:
            report += f"- {strength}\n"
        
        # Identify recommendations based on scores
        report += "\n### Recommendations\n\n"
        recommendations = []
        
        if exchange_count < 4:
            recommendations.append("Increase the number of exchanges with the AI")
        
        if prompt_progression.get('progression_score', 0) < 5:
            recommendations.append("Improve prompt engineering by refining prompts based on previous responses")
        
        if critical_eval.get('critical_eval_score', 0) < 5:
            recommendations.append("Enhance critical evaluation by providing more specific feedback on AI-generated content")
        
        if impl_improvements.get('implementation_score', 0) < 5:
            recommendations.append("Demonstrate more implementation improvements by showing how you've modified or enhanced AI suggestions")
        
        # Check for specific areas of improvement
        if avg_assistant_score < 6:
            recommendations.append("Work on crafting more effective prompts to elicit higher quality AI responses")
        
        if code_blocks_count < 2:
            recommendations.append("Request more code examples or technical details from the AI")
        
        if not recommendations:
            recommendations.append("Continue current approach to AI interaction")
        
        for recommendation in recommendations:
            report += f"- {recommendation}\n"
        
        # Save report if output file provided
        if output_file:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to {output_file}")
        
        return report
    
    def generate_visualization(self, analysis, output_dir=None):
        """
        Generate visualization charts for a conversation analysis.
        
        Args:
            analysis: Dictionary with conversation analysis
            output_dir: Directory to save visualization files (optional)
            
        Returns:
            List of generated visualization file paths
        """
        if not analysis:
            return []
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = self.output_dir
        
        file_name = analysis.get('file_name', 'conversation').replace('.txt', '').replace('.json', '').replace('.md', '')
        metrics = analysis.get('metrics', {})
        rubric_scores = analysis.get('rubric_scores', {})
        
        visualization_files = []
        
        # 1. Create radar chart of rubric scores
        try:
            plt.figure(figsize=(10, 8))
            
            categories = ['AI Interactions', 'Prompt Engineering', 'Critical Evaluation', 'Implementation']
            
            values = [
                rubric_scores.get('ai_interactions', {}).get('percentage', 0) / 100,
                rubric_scores.get('prompt_engineering', {}).get('percentage', 0) / 100,
                rubric_scores.get('critical_evaluation', {}).get('percentage', 0) / 100,
                rubric_scores.get('implementation_improvements', {}).get('percentage', 0) / 100
            ]
            
            # Create angles for each category
            N = len(categories)
            angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
            angles += angles[:1]  # Close the polygon
            values += values[:1]  # Close the polygon
            
            # Plot radar chart
            ax = plt.subplot(111, polar=True)
            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            
            # Add category labels and grid
            ax.set_thetagrids(np.degrees(angles[:-1]), categories)
            
            # Add percentage labels
            for angle, value in zip(angles, values):
                if angle < 2*np.pi:  # Skip the duplicated last point
                    plt.annotate(f"{value*100:.1f}%",
                              xy=(angle, value),
                              xytext=(angle, value + 0.1),
                              ha='center')
            
            # Set y-axis limits
            ax.set_ylim(0, 1.0)
            
            # Add percentage ticks and grid
            ax.set_rticks([0.25, 0.5, 0.75, 1.0])
            ax.set_yticklabels(['25%', '50%', '75%', '100%'])
            ax.grid(True)
            
            # Add title
            plt.title(f"Rubric Scores: {file_name}", size=15, y=1.1)
            
            # Save figure
            radar_chart_path = os.path.join(output_dir, f"{file_name}_radar_chart.png")
            plt.tight_layout()
            plt.savefig(radar_chart_path)
            plt.close()
            
            visualization_files.append(radar_chart_path)
            print(f"Radar chart saved to {radar_chart_path}")
        except Exception as e:
            print(f"Error creating radar chart: {e}")
        
        # 2. Create progression chart of prompt quality
        try:
            prompt_progression = metrics.get('prompt_progression', {})
            prompt_scores = prompt_progression.get('prompt_scores', [])
            
            if prompt_scores:
                plt.figure(figsize=(10, 6))
                
                exchanges = range(1, len(prompt_scores) + 1)
                
                plt.plot(exchanges, prompt_scores, 'o-', linewidth=2, color='blue')
                
                # Add trendline
                if len(prompt_scores) > 1:
                    z = np.polyfit(exchanges, prompt_scores, 1)
                    p = np.poly1d(z)
                    plt.plot(exchanges, p(exchanges), "r--", alpha=0.8, label=f"Trend: {z[0]:.2f}x + {z[1]:.2f}")
                
                # Add labels and grid
                plt.xlabel('Exchange Number')
                plt.ylabel('Prompt Quality Score (0-10)')
                plt.title(f"Prompt Quality Progression: {file_name}")
                plt.grid(True, alpha=0.3)
                plt.xticks(exchanges)
                plt.ylim(0, 10)
                
                if len(prompt_scores) > 1:
                    plt.legend()
                
                # Save figure
                progression_chart_path = os.path.join(output_dir, f"{file_name}_prompt_progression.png")
                plt.tight_layout()
                plt.savefig(progression_chart_path)
                plt.close()
                
                visualization_files.append(progression_chart_path)
                print(f"Progression chart saved to {progression_chart_path}")
        except Exception as e:
            print(f"Error creating progression chart: {e}")
        
        # 3. Create bar chart comparing all 4 rubric components
        try:
            plt.figure(figsize=(10, 6))
            
            categories = ['AI Interactions', 'Prompt Engineering', 'Critical Evaluation', 'Implementation']
            
            scores = [
                rubric_scores.get('ai_interactions', {}).get('points', 0),
                rubric_scores.get('prompt_engineering', {}).get('points', 0),
                rubric_scores.get('critical_evaluation', {}).get('points', 0),
                rubric_scores.get('implementation_improvements', {}).get('points', 0)
            ]
            
            max_scores = [5, 5, 5, 5]  # Max points for each category
            
            # Calculate percentages for normalized comparison
            percentages = [score / max_score * 100 for score, max_score in zip(scores, max_scores)]
            
            # Set color based on percentage
            colors = []
            for percentage in percentages:
                if percentage >= 75:
                    colors.append('#4CAF50')  # Green - Distinction
                elif percentage >= 65:
                    colors.append('#8BC34A')  # Light Green - Credit
                elif percentage >= 50:
                    colors.append('#FFC107')  # Amber - Pass
                else:
                    colors.append('#FF5722')  # Deep Orange - Fail
            
            # Create bar chart
            bars = plt.bar(categories, scores, color=colors)
            
            # Add data labels
            for bar, score, percentage in zip(bars, scores, percentages):
                plt.text(bar.get_x() + bar.get_width()/2., 
                        bar.get_height() + 0.1,
                        f"{score:.2f} ({percentage:.1f}%)",
                        ha='center')
            
            # Add max score line
            plt.axhline(y=5, color='r', linestyle='--', alpha=0.5, label='Max Score (5)')
            
            # Add distinction threshold line (3.75 points = 75%)
            plt.axhline(y=3.75, color='g', linestyle='--', alpha=0.5, label='Distinction Threshold (3.75)')
            
            # Add credit threshold line (3.25 points = 65%)
            plt.axhline(y=3.25, color='y', linestyle='--', alpha=0.5, label='Credit Threshold (3.25)')
            
            # Add pass threshold line (2.5 points = 50%)
            plt.axhline(y=2.5, color='orange', linestyle='--', alpha=0.5, label='Pass Threshold (2.5)')
            
            # Add labels and grid
            plt.xlabel('Rubric Category')
            plt.ylabel('Points (out of 5)')
            plt.title(f"Rubric Assessment: {file_name}")
            plt.grid(True, axis='y', alpha=0.3)
            plt.ylim(0, 5.5)
            plt.legend()
            
            # Save figure
            bar_chart_path = os.path.join(output_dir, f"{file_name}_rubric_assessment.png")
            plt.tight_layout()
            plt.savefig(bar_chart_path)
            plt.close()
            
            visualization_files.append(bar_chart_path)
            print(f"Bar chart saved to {bar_chart_path}")
        except Exception as e:
            print(f"Error creating bar chart: {e}")
        
        return visualization_files
    
    def analyze_folder(self, folder_path):
        """
        Analyze all conversation files in a folder.
        
        Args:
            folder_path: Path to folder containing conversation files
            
        Returns:
            List of analysis results
        """
        # Get all text files in the folder
        text_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.txt', '.json','.md')):
                    text_files.append(os.path.join(root, file))
        
        print(f"Found {len(text_files)} conversation files")
        
        # Analyze each file
        all_results = []
        
        for file_path in text_files:
            print(f"\nAnalyzing {file_path}...")
            
            # Analyze the conversation
            analysis = self.analyze_conversation_file(file_path)
            
            if analysis:
                # Generate report
                report_file = os.path.join(self.output_dir, f"{os.path.basename(file_path)}_report.md")
                self.generate_report(analysis, report_file)
                
                # Generate visualizations
                self.generate_visualization(analysis)
                
                all_results.append(analysis)
            else:
                print(f"No valid analysis generated for {file_path}")
        
        # Generate summary report
        if all_results:
            self.generate_summary_report(all_results)
        
        return all_results
    
    def generate_summary_report(self, all_results):
        """
        Generate a summary report for all analyzed conversations.
        
        Args:
            all_results: List of analysis results
            
        Returns:
            Path to the generated summary report
        """
        if not all_results:
            return None
        
        summary_file = os.path.join(self.output_dir, "summary_report.md")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# AI Conversation Analysis Summary Report\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total conversations analyzed: {len(all_results)}\n\n")
            
            # Create summary table
            f.write("## Summary of Results\n\n")
            f.write("| Conversation | Exchanges | AI Interactions | Prompt Engineering | Critical Evaluation | Implementation | Total |\n")
            f.write("|--------------|-----------|----------------|-------------------|---------------------|----------------|-------|\n")
            
            # Sort by total score (highest first)
            sorted_results = sorted(all_results, key=lambda x: x.get('rubric_scores', {}).get('total', {}).get('points', 0), reverse=True)
            
            for result in sorted_results:
                file_name = result.get('file_name', 'Unknown')
                exchanges = result.get('metrics', {}).get('exchange_count', 0)
                
                rubric_scores = result.get('rubric_scores', {})
                ai_points = rubric_scores.get('ai_interactions', {}).get('points', 0)
                prompt_points = rubric_scores.get('prompt_engineering', {}).get('points', 0)
                eval_points = rubric_scores.get('critical_evaluation', {}).get('points', 0)
                impl_points = rubric_scores.get('implementation_improvements', {}).get('points', 0)
                total_points = rubric_scores.get('total', {}).get('points', 0)
                
                f.write(f"| {file_name} | {exchanges} | {ai_points:.2f}/5 | {prompt_points:.2f}/5 | {eval_points:.2f}/5 | {impl_points:.2f}/5 | {total_points:.2f}/20 |\n")
            
            # Calculate average scores
            avg_ai_points = sum(r.get('rubric_scores', {}).get('ai_interactions', {}).get('points', 0) for r in all_results) / len(all_results)
            avg_prompt_points = sum(r.get('rubric_scores', {}).get('prompt_engineering', {}).get('points', 0) for r in all_results) / len(all_results)
            avg_eval_points = sum(r.get('rubric_scores', {}).get('critical_evaluation', {}).get('points', 0) for r in all_results) / len(all_results)
            avg_impl_points = sum(r.get('rubric_scores', {}).get('implementation_improvements', {}).get('points', 0) for r in all_results) / len(all_results)
            avg_total_points = sum(r.get('rubric_scores', {}).get('total', {}).get('points', 0) for r in all_results) / len(all_results)
            
            f.write(f"| **Average** | - | {avg_ai_points:.2f}/5 | {avg_prompt_points:.2f}/5 | {avg_eval_points:.2f}/5 | {avg_impl_points:.2f}/5 | {avg_total_points:.2f}/20 |\n\n")
            
            # Distribution of performance levels
            f.write("## Performance Level Distribution\n\n")
            
            categories = [
                ('ai_interactions', 'AI Interactions'),
                ('prompt_engineering', 'Prompt Engineering'),
                ('critical_evaluation', 'Critical Evaluation'),
                ('implementation_improvements', 'Implementation Improvements')
            ]
            
            for category_key, category_name in categories:
                f.write(f"### {category_name}\n\n")
                
                # Count performance levels
                levels = {
                    'Distinction (75-100%)': 0,
                    'Credit (65-74%)': 0,
                    'Pass (50-64%)': 0,
                    'Fail (0-49%)': 0
                }
                
                for result in all_results:
                    level = result.get('rubric_scores', {}).get(category_key, {}).get('level', 'Fail (0-49%)')
                    levels[level] += 1
                
                # Create distribution table
                f.write("| Performance Level | Count | Percentage |\n")
                f.write("|-------------------|-------|------------|\n")
                
                for level, count in levels.items():
                    percentage = count / len(all_results) * 100
                    f.write(f"| {level} | {count} | {percentage:.1f}% |\n")
                
                f.write("\n")
            
            # Correlation analysis
            f.write("## Correlation Analysis\n\n")
            
            # Calculate correlations between different metrics
            correlations = []
            
            # Collect metric pairs to analyze correlation
            metric_pairs = [
                ('ai_interactions', 'prompt_engineering', 'AI Interactions vs. Prompt Engineering'),
                ('ai_interactions', 'critical_evaluation', 'AI Interactions vs. Critical Evaluation'),
                ('ai_interactions', 'implementation_improvements', 'AI Interactions vs. Implementation'),
                ('prompt_engineering', 'critical_evaluation', 'Prompt Engineering vs. Critical Evaluation'),
                ('prompt_engineering', 'implementation_improvements', 'Prompt Engineering vs. Implementation'),
                ('critical_evaluation', 'implementation_improvements', 'Critical Evaluation vs. Implementation')
            ]
            
            for metric1, metric2, label in metric_pairs:
                values1 = [r.get('rubric_scores', {}).get(metric1, {}).get('points', 0) for r in all_results]
                values2 = [r.get('rubric_scores', {}).get(metric2, {}).get('points', 0) for r in all_results]
                
                if len(values1) > 1 and len(values2) > 1:
                    correlation = np.corrcoef(values1, values2)[0, 1]
                    correlations.append((label, correlation))
            
            if correlations:
                f.write("| Metrics | Correlation Coefficient |\n")
                f.write("|---------|---------------------------|\n")
                
                for label, correlation in correlations:
                    f.write(f"| {label} | {correlation:.3f} |\n")
                
                f.write("\n")
                
                # Analysis of correlations
                f.write("### Interpretation\n\n")
                
                strong_correlations = [(label, corr) for label, corr in correlations if abs(corr) > 0.7]
                moderate_correlations = [(label, corr) for label, corr in correlations if 0.4 < abs(corr) <= 0.7]
                weak_correlations = [(label, corr) for label, corr in correlations if abs(corr) <= 0.4]
                
                if strong_correlations:
                    f.write("**Strong Correlations (|r| > 0.7):**\n\n")
                    for label, corr in strong_correlations:
                        direction = "positive" if corr > 0 else "negative"
                        f.write(f"- {label}: {corr:.3f} ({direction})\n")
                    f.write("\n")
                
                if moderate_correlations:
                    f.write("**Moderate Correlations (0.4 < |r| <= 0.7):**\n\n")
                    for label, corr in moderate_correlations:
                        direction = "positive" if corr > 0 else "negative"
                        f.write(f"- {label}: {corr:.3f} ({direction})\n")
                    f.write("\n")
                
                if weak_correlations:
                    f.write("**Weak Correlations (|r| <= 0.4):**\n\n")
                    for label, corr in weak_correlations:
                        direction = "positive" if corr > 0 else "negative"
                        f.write(f"- {label}: {corr:.3f} ({direction})\n")
                    f.write("\n")
            
            # Overall insights
            f.write("## Overall Insights\n\n")
            
            # Performance distribution
            total_distinctions = sum(1 for r in all_results if r.get('rubric_scores', {}).get('total', {}).get('percentage', 0) >= 75)
            total_credits = sum(1 for r in all_results if 65 <= r.get('rubric_scores', {}).get('total', {}).get('percentage', 0) < 75)
            total_passes = sum(1 for r in all_results if 50 <= r.get('rubric_scores', {}).get('total', {}).get('percentage', 0) < 65)
            total_fails = sum(1 for r in all_results if r.get('rubric_scores', {}).get('total', {}).get('percentage', 0) < 50)
            
            f.write(f"- **Distinction Level:** {total_distinctions} conversations ({total_distinctions/len(all_results)*100:.1f}%)\n")
            f.write(f"- **Credit Level:** {total_credits} conversations ({total_credits/len(all_results)*100:.1f}%)\n")
            f.write(f"- **Pass Level:** {total_passes} conversations ({total_passes/len(all_results)*100:.1f}%)\n")
            f.write(f"- **Fail Level:** {total_fails} conversations ({total_fails/len(all_results)*100:.1f}%)\n\n")
            
            # Strongest and weakest areas
            avg_scores = [
                ('AI Interactions', avg_ai_points),
                ('Prompt Engineering', avg_prompt_points),
                ('Critical Evaluation', avg_eval_points),
                ('Implementation Improvements', avg_impl_points)
            ]
            
            sorted_scores = sorted(avg_scores, key=lambda x: x[1], reverse=True)
            
            f.write("### Strongest and Weakest Areas\n\n")
            f.write(f"**Strongest Area:** {sorted_scores[0][0]} (Average: {sorted_scores[0][1]:.2f}/5)\n")
            f.write(f"**Weakest Area:** {sorted_scores[-1][0]} (Average: {sorted_scores[-1][1]:.2f}/5)\n\n")
            
            # Recommendations based on analysis
            f.write("### Recommendations\n\n")
            
            # Add general recommendations based on weakest areas
            if sorted_scores[-1][0] == 'AI Interactions':
                f.write("- Focus on increasing the number and quality of AI exchanges\n")
                f.write("- Work on creating more sophisticated problem-solving approaches with AI\n")
            elif sorted_scores[-1][0] == 'Prompt Engineering':
                f.write("- Improve prompt engineering skills by creating more specific and refined prompts\n")
                f.write("- Show clearer progression in prompt quality throughout conversations\n")
            elif sorted_scores[-1][0] == 'Critical Evaluation':
                f.write("- Enhance critical evaluation of AI outputs with more specific feedback\n")
                f.write("- Demonstrate deeper technical understanding when analyzing AI-generated content\n")
            elif sorted_scores[-1][0] == 'Implementation Improvements':
                f.write("- Show more substantial improvements beyond what the AI suggested\n")
                f.write("- Demonstrate your own technical expertise through code modifications and enhancements\n")
            
            f.write("\n### Most Common Strengths\n\n")
            
            # Collect all strengths from individual reports
            all_strengths = []
            for result in all_results:
                metrics = result.get('metrics', {})
                exchange_count = metrics.get('exchange_count', 0)
                
                # Simplified strength detection based on key metrics
                if exchange_count >= 5:
                    all_strengths.append("Good number of AI exchanges")
                
                prompt_progression = metrics.get('prompt_progression', {})
                if prompt_progression.get('progression_score', 0) > 6:
                    all_strengths.append("Strong prompt engineering progression")
                
                critical_eval = metrics.get('critical_evaluation', {})
                if critical_eval.get('critical_eval_score', 0) > 6:
                    all_strengths.append("Effective critical evaluation")
                
                impl_improvements = metrics.get('implementation_improvements', {})
                if impl_improvements.get('implementation_score', 0) > 6:
                    all_strengths.append("Substantial implementation improvements")
            
            # Count and report top strengths
            strength_counts = Counter(all_strengths)
            
            for strength, count in strength_counts.most_common(3):  # Top 3 strengths
                percentage = count / len(all_results) * 100
                f.write(f"- {strength}: Found in {count} conversations ({percentage:.1f}%)\n")
            
            f.write("\n### Most Common Areas for Improvement\n\n")
            
            # Collect all improvement areas from individual reports
            all_improvements = []
            for result in all_results:
                metrics = result.get('metrics', {})
                exchange_count = metrics.get('exchange_count', 0)
                
                # Simplified improvement detection based on key metrics
                if exchange_count < 4:
                    all_improvements.append("Increase number of AI exchanges")
                
                prompt_progression = metrics.get('prompt_progression', {})
                if prompt_progression.get('progression_score', 0) < 5:
                    all_improvements.append("Improve prompt engineering progression")
                
                critical_eval = metrics.get('critical_evaluation', {})
                if critical_eval.get('critical_eval_score', 0) < 5:
                    all_improvements.append("Enhance critical evaluation")
                
                impl_improvements = metrics.get('implementation_improvements', {})
                if impl_improvements.get('implementation_score', 0) < 5:
                    all_improvements.append("Demonstrate more implementation improvements")
            
            # Count and report top improvement areas
            improvement_counts = Counter(all_improvements)
            
            for improvement, count in improvement_counts.most_common(3):  # Top 3 improvement areas
                percentage = count / len(all_results) * 100
                f.write(f"- {improvement}: Needed in {count} conversations ({percentage:.1f}%)\n")
        
        print(f"Summary report saved to {summary_file}")
        return summary_file

    # [Existing imports and class definition remain the same]
# ... (previous code of AIConversationAnalyzer class) ...

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Analyze AI conversation files from a specified folder.")
    parser.add_argument("folder_path", type=str, help="Path to the folder containing conversation files (text or JSON).")
    parser.add_argument("--output_dir", type=str, default="ai_conversation_analysis_reports", help="Directory to save analysis reports and visualizations (default: ai_conversation_analysis_reports).")

    # Parse arguments
    args = parser.parse_args()

    # Initialize the analyzer with the specified output directory
    analyzer = AIConversationAnalyzer(output_dir=args.output_dir)

    # Analyze the folder
    print(f"Starting analysis of conversations in: {args.folder_path}")
    print(f"Output will be saved to: {analyzer.output_dir}")
    
    analysis_results = analyzer.analyze_folder(args.folder_path)

    if analysis_results:
        print(f"\nAnalysis complete. {len(analysis_results)} conversations processed.")
        print(f"Reports and visualizations are saved in '{analyzer.output_dir}'.")
    else:
        print("\nNo conversations were successfully analyzed.")
