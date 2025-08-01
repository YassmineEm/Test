from utils import db, qdrant_client, embedding_utils
from utils.openai_client import ask_openai
from bson import ObjectId  

async def handle_chat(question: str):
  
    question_embedding = embedding_utils.generate_embedding(question)

    
    search_result = qdrant_client.qdrant.search(
        collection_name="documents",
        query_vector=question_embedding,
        limit=3
    )

   
    context_parts = []
    for hit in search_result:
        try:
            mongo_id = hit.payload.get("mongo_id")
            if mongo_id:
                document = db.db.documents.find_one({"_id": ObjectId(mongo_id)})
                if document and "content" in document:
                    context_parts.append(document["content"])
        except Exception as e:
            print(f"Erreur récupération document {hit.id}: {e}")

    context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

  
    messages = [
        {"role": "system", "content": "You are an AI assistant helping users based on uploaded documents."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]

    
    answer = ask_openai(messages)

   
    db.db.chat_histories.insert_one({
        "question": question,
        "answer": answer,
        "context": context
    })

    # 7. Retour de la réponse
    return {"answer": answer}

