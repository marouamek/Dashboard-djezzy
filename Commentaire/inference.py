# Importation des classes nécessaires depuis la bibliothèque Transformers et de la bibliothèque PyTorch
from transformers import CamembertTokenizer, CamembertForSequenceClassification
import torch  # type: ignore

# Chargement du modèle
chemin_modele = "Commentaire/camembert-comment-classifier"

tokenizer = CamembertTokenizer.from_pretrained(chemin_modele)
modele = CamembertForSequenceClassification.from_pretrained(chemin_modele)

# Map label ID → (sentiment, thème)
ID2LABEL = {
    0: ("NEGATIF", "APPEL"),
    1: ("NEGATIF", "AUTRE"),
    2: ("NEGATIF", "INTERNET"),
    3: ("NEGATIF", "OFFRE ET SERVICE"),
    4: ("NEGATIF", "PRIX ET TARIFICATION"),
    5: ("NEGATIF", "SERVICE CLIENT"),
    6: ("NEUTRE", "APPEL"),
    7: ("NEUTRE", "AUTRE"),
    8: ("NEUTRE", "INTERNET"),
    9: ("NEUTRE", "OFFRE ET SERVICE"),
    10: ("NEUTRE", "PRIX ET TARIFICATION"),
    11: ("NEUTRE", "SERVICE CLIENT"),
    12: ("POSITIF", "APPEL"),
    13: ("POSITIF", "AUTRE"),
    14: ("POSITIF", "INTERNET"),
    15: ("POSITIF", "OFFRE ET SERVICE"),
    16: ("POSITIF", "PRIX ET TARIFICATION"),
    17: ("POSITIF", "SERVICE CLIENT")
}

def analyse_commentaire(commentaire):
    inputs = tokenizer(commentaire, return_tensors="pt", truncation=True, padding=True) # tokenize the input text to prepare it for the model 
    outputs = modele(**inputs)
    logits = outputs.logits
    probs = torch.nn.functional.softmax(logits, dim=1)
    top_idx = torch.argmax(probs).item()
    confidence = probs[0, top_idx].item()
    sentiment, theme = ID2LABEL[top_idx]
    
    return {
        "sentiment": sentiment,
        "theme": theme,
        "label_id": top_idx,
        "score": round(confidence, 4)
    }