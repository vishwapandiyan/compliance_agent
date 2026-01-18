import re
from typing import List, Dict, Tuple
import os

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class CodeChunkFilter:
   
    
    def __init__(self):
       
        self.model = None
        if EMBEDDINGS_AVAILABLE:
            try:
               
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Warning: Could not load embedding model: {e}")
                self.model = None
    
    def extract_code_chunks(self, file_content: str, file_name: str, chunk_size: int = 20) -> List[Dict]:
      
        lines = file_content.split('\n')
        chunks = []
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_text = '\n'.join(chunk_lines)
            start_line = i + 1
            end_line = min(i + chunk_size, len(lines))
            
            chunks.append({
                'text': chunk_text,
                'start_line': start_line,
                'end_line': end_line,
                'file_name': file_name
            })
        
        return chunks
    
    def filter_risky_chunks(self, chunks: List[Dict]) -> List[Dict]:
        
        risky_patterns = [
            r'password\s*[:=]\s*["\'][^"\']+["\']',  
            r'api[_-]?key\s*[:=]\s*["\'][^"\']+["\']',  
            r'token\s*[:=]\s*["\'][^"\']+["\']',  
            r'secret\s*[:=]\s*["\'][^"\']+["\']',  
            r'STRIPE[_-]?SECRET[_-]?KEY', 
            r'SENDGRID[_-]?API[_-]?KEY', 
            r'"password":\s*"',  
            r':\s*true\s*[,}]',  
            r'\.read\s*:\s*true',  
            r'\.write\s*:\s*true', 
            r'"\.read":\s*true',  
            r'"\.write":\s*true', 
            r'0\.0\.0\.0/0',  
            r'CidrIp:\s*0\.0\.0\.0/0',  
            r'eval\s*\(', 
            r'exec\s*\(',  
            r'SELECT.*\+.*FROM', 
            r'f["\'].*SELECT.*\{.*\}', 
            r'os\.system\s*\(',  
            r'subprocess\.call',  
            r'pickle\.loads', 
            r'yaml\.load\s*\(',  
            r'debug\s*=\s*True',  
            r'CORS\(.*allow_origins.*\*', 
            r'ENCRYPTION[_-]?KEY\s*=',  
            r'SECRET[_-]?KEY\s*=',  
        ]
        
        risky_chunks = []
        for chunk in chunks:
            chunk_text = chunk['text'] 
            chunk_text_lower = chunk_text.lower()
            
            
            for pattern in risky_patterns:
                if re.search(pattern, chunk_text, re.IGNORECASE):
                    risky_chunks.append(chunk)
                    break  
        return risky_chunks
    
    def rank_chunks_by_risk(self, chunks: List[Dict]) -> List[Dict]:
       
        def calculate_risk_score(chunk: Dict) -> int:
            text = chunk['text'].lower()
            score = 0
            
           
            high_risk_patterns = [
                r'password\s*=', r'api[_-]?key\s*=', r'secret\s*=', r'token\s*=',
                r'eval\s*\(', r'exec\s*\(', r'0\.0\.0\.0/0', r'\.read\s*=\s*true'
            ]
            for pattern in high_risk_patterns:
                if re.search(pattern, text):
                    score += 10
            
            # Medium-risk patterns
            medium_risk_patterns = [
                r'SELECT.*\+', r'f["\'].*\{.*\}', r'os\.system', r'debug\s*=\s*True'
            ]
            for pattern in medium_risk_patterns:
                if re.search(pattern, text):
                    score += 5
            
            return score
        
       
        scored_chunks = [(chunk, calculate_risk_score(chunk)) for chunk in chunks]
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return [chunk for chunk, score in scored_chunks if score > 0]
    
    def get_risky_code_sections(self, file_content: str, file_name: str) -> List[Dict]:
       
        
        chunks = self.extract_code_chunks(file_content, file_name, chunk_size=15)
        
       
        risky_chunks = self.filter_risky_chunks(chunks)
        
       
        if not risky_chunks:
          
            security_keywords = ['password', 'secret', 'key', 'token', 'auth', 'permission', 'access', 'config', 
                                'stripe', 'sendgrid', 'api_key', 'secret_key', 'encryption', '0.0.0.0', 
                                '.read', '.write', 'cidrip', 'database', 'credentials']
            for chunk in chunks:
                chunk_lower = chunk['text'].lower()
               
                if any(keyword in chunk_lower for keyword in security_keywords):
                    risky_chunks.append(chunk)
        
        
        config_file_names = ['config', 'env', 'firebase', 'aws', '.yml', '.yaml', '.json']
        if not risky_chunks:
            if any(name in file_name.lower() for name in config_file_names):
                
                risky_chunks = chunks[:5]
            elif len(chunks) > 0 and len(chunks) <= 3:
                
                risky_chunks = chunks
        
       
        ranked_chunks = self.rank_chunks_by_risk(risky_chunks) if risky_chunks else risky_chunks
        
       
        return ranked_chunks if ranked_chunks else []

