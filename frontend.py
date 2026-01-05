import streamlit as st
import requests
import json

# --- CONFIGURATION ---
# Remplace cette URL par la VRAIE URL de ton API Azure
# Exemple: "https://mon-projet-mlops.azurewebsites.net/predict"
API_URL = "https://bank-churn.whitemoss-5d9e8f98.francecentral.azurecontainerapps.io/predict" 

st.title("🏦 Prédiction de Churn Bancaire")
st.write("Entrez les informations du client pour savoir s'il va quitter la banque.")

# --- FORMULAIRE ---
# On crée des colonnes pour faire joli
col1, col2 = st.columns(2)

with col1:
    credit_score = st.number_input("Score de Crédit", min_value=300, max_value=850, value=600)
    geography = st.selectbox("Pays", ["France", "Germany", "Spain"])
    gender = st.selectbox("Genre", ["Male", "Female"])
    age = st.number_input("Age", min_value=18, max_value=100, value=30)
    tenure = st.number_input("Années de fidélité", min_value=0, max_value=10, value=3)

with col2:
    balance = st.number_input("Solde du compte ($)", min_value=0.0, value=10000.0)
    num_of_products = st.slider("Nombre de produits", 1, 4, 1)
    has_cr_card = st.selectbox("A une carte de crédit ?", [0, 1], format_func=lambda x: "Oui" if x == 1 else "Non")
    is_active_member = st.selectbox("Est membre actif ?", [0, 1], format_func=lambda x: "Oui" if x == 1 else "Non")
    estimated_salary = st.number_input("Salaire Estimé ($)", min_value=0.0, value=50000.0)

# --- BOUTON DE PREDICTION ---
# --- BOUTON DE PREDICTION ---
if st.button("🔮 Lancer la prédiction"):
    
    # 1. Conversion des données (Pré-traitement)
    # On transforme le pays choisi en deux colonnes de 0 ou 1
    geo_germany = 1 if geography == "Germany" else 0
    geo_spain = 1 if geography == "Spain" else 0
    
    # 2. Préparation du JSON strict (exactement les champs que tu m'as montrés)
    input_data = {
        "CreditScore": credit_score,
        "Age": age,
        "Tenure": tenure,
        "Balance": balance,
        "NumOfProducts": num_of_products,
        "HasCrCard": has_cr_card,
        "IsActiveMember": is_active_member,
        "EstimatedSalary": estimated_salary,
        "Geography_Germany": geo_germany,
        "Geography_Spain": geo_spain
    }
    
    # Note : J'ai retiré "Gender" car il n'était pas dans ta liste d'erreur.
    # Si l'API renvoie une erreur "Missing Gender_Male", dis-le moi !

    st.text("Envoi des données transformées à l'API...")
    
    try:
        response = requests.post(API_URL, json=input_data)
        
        if response.status_code == 200:
            result = response.json()
            # On récupère la prédiction (adapte la clé "prediction" si besoin)
            # Parfois c'est "result", "churn_prediction", etc. Regarde le JSON affiché.
            st.success("✅ Réponse reçue du serveur !")
            st.json(result) # On affiche le résultat brut pour être sûr
            
        else:
            st.error(f"Erreur API : {response.status_code}")
            st.warning("Détails de l'erreur :")
            st.json(response.json())
            
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")