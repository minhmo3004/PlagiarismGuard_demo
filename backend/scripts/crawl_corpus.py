"""
Main Corpus Crawler
Orchestrates crawling from multiple sources and saves to Redis
"""
import sys
import os
import json
import redis
from typing import List, Dict
from datetime import datetime

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Load .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

# Import crawlers from same directory
from crawlers.arxiv_crawler import ArxivCrawler
from crawlers.viwiki_crawler import ViWikiCrawler

# Import app modules
from app.services.preprocessing.text_normalizer import normalize_text
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.algorithm.shingling import create_shingles
from app.services.algorithm.minhash import create_minhash_signature
from app.config import settings


class CorpusCrawler:
    """Main crawler that orchestrates multiple sources"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=False
        )
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            print("✅ Connected to Redis")
        except:
            print("❌ Cannot connect to Redis!")
            sys.exit(1)
    
    def crawl_all(self, target: int = 2000):
        """
        Crawl from all sources
        
        Target distribution:
        - arXiv: 40% (800 docs)
        - Vietnamese Wikipedia: 40% (800 docs)
        - Others: 20% (400 docs)
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting corpus crawl - Target: {target} documents")
        print(f"{'='*60}\n")
        
        all_documents = []
        
        # Calculate targets
        arxiv_target = int(target * 0.4)
        viwiki_target = int(target * 0.4)
        
        # 1. Crawl arXiv
        print("\n📚 Phase 1: arXiv Papers")
        print("-" * 60)
        arxiv = ArxivCrawler()
        arxiv_docs = arxiv.crawl(limit=arxiv_target)
        all_documents.extend(arxiv_docs)
        
        # 2. Crawl Vietnamese Wikipedia
        print("\n📖 Phase 2: Vietnamese Wikipedia")
        print("-" * 60)
        viwiki = ViWikiCrawler()
        viwiki_docs = viwiki.crawl(limit=viwiki_target)
        all_documents.extend(viwiki_docs)
        
        print(f"\n{'='*60}")
        print(f"📊 Crawl Summary")
        print(f"{'='*60}")
        print(f"arXiv: {len(arxiv_docs)} documents")
        print(f"Vietnamese Wikipedia: {len(viwiki_docs)} documents")
        print(f"Total: {len(all_documents)} documents")
        print(f"{'='*60}\n")
        
        return all_documents
    
    def save_to_redis(self, documents: List[Dict]):
        """Save documents to Redis corpus"""
        print(f"\n💾 Saving {len(documents)} documents to Redis...")
        
        saved = 0
        skipped = 0
        
        for i, doc in enumerate(documents):
            try:
                # Generate unique doc ID with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                doc_id = f"crawled_{timestamp}_{i:05d}"
                
                # Check if already exists (shouldn't happen with timestamp, but just in case)
                if self.redis_client.exists(f"doc:sig:{doc_id}"):
                    skipped += 1
                    continue
                
                # Process text
                text = normalize_text(doc['content'])
                tokens = preprocess_vietnamese(text)
                shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
                minhash = create_minhash_signature(shingles)
                
                # Store signature
                sig_json = json.dumps(minhash.hashvalues.tolist())
                self.redis_client.set(f"doc:sig:{doc_id}", sig_json)
                
                # Store metadata
                metadata = {
                    "title": doc['title'],
                    "author": doc['author'],
                    "university": doc['university'],
                    "year": doc.get('year'),
                    "source": doc['source'],
                    "word_count": len(tokens)
                }
                self.redis_client.set(f"doc:meta:{doc_id}", json.dumps(metadata))
                
                saved += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Progress: {i + 1}/{len(documents)} ({saved} saved, {skipped} skipped)")
                    
            except Exception as e:
                print(f"  ⚠️  Error saving doc {i}: {e}")
                continue
        
        print(f"\n✅ Saved {saved} documents to Redis")
        print(f"⏭️  Skipped {skipped} duplicates\n")
        
        return saved


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl academic corpus')
    parser.add_argument('--target', type=int, default=2000, help='Target number of documents')
    parser.add_argument('--test', action='store_true', help='Test mode (only 20 docs)')
    
    args = parser.parse_args()
    
    if args.test:
        target = 20
        print("\n🧪 TEST MODE - Crawling only 20 documents\n")
    else:
        target = args.target
    
    crawler = CorpusCrawler()
    
    # Crawl
    documents = crawler.crawl_all(target=target)
    
    # Save to Redis
    if documents:
        crawler.save_to_redis(documents)
        
        # Show final stats
        print("\n" + "="*60)
        print("🎉 Crawl Complete!")
        print("="*60)
        print(f"Total documents in corpus: {len(crawler.redis_client.keys('doc:sig:*'))}")
        print("="*60 + "\n")
    else:
        print("\n❌ No documents crawled!\n")


if __name__ == "__main__":
    main()
