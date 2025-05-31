import streamlit as st
import sqlite3
import pandas as pd

# -------------------- Connexion à la base --------------------
def connect_db():
    conn = sqlite3.connect("database.db")
    return conn

# -------------------- Clients --------------------
def get_clients():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM Client", conn)
    conn.close()
    return df

def insert_client(adresse, ville, code_postal, email, telephone, nom):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Client (adresse, ville, code_postal, email, telephone, nom)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (adresse, ville, code_postal, email, telephone, nom))
    conn.commit()
    conn.close()

# -------------------- Réservations --------------------
def get_reservations():
    conn = connect_db()
    query = """
    SELECT Reservation.id, Client.nom AS client, Reservation.date_debut, Reservation.date_fin
    FROM Reservation
    JOIN Client ON Reservation.client_id = Client.id
    ORDER BY Reservation.date_debut;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def insert_reservation(date_debut, date_fin, client_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Reservation (date_debut, date_fin, client_id)
        VALUES (?, ?, ?)
    """, (date_debut, date_fin, client_id))
    conn.commit()
    conn.close()

# -------------------- Chambres disponibles --------------------
def get_chambres_disponibles(start_date, end_date):
    conn = connect_db()
    query = """
    SELECT Chambre.id, Chambre.numero, Chambre.etage, TypeChambre.nom AS type
    FROM Chambre
    JOIN TypeChambre ON Chambre.type_id = TypeChambre.id
    WHERE Chambre.id NOT IN (
        SELECT Chambre.id
        FROM Reservation
        JOIN Chambre ON Chambre.id = Reservation.id
        WHERE NOT (
            Reservation.date_fin < ? OR Reservation.date_debut > ?
        )
    );
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    return df

# -------------------- Interface principale --------------------
st.set_page_config(page_title="Gestion Hôtel", layout="centered")
st.title("🏨 Interface de gestion d'hôtel")

st.markdown("## 👤 Clients")
clients_df = get_clients()
st.dataframe(clients_df)

with st.expander("➕ Ajouter un client"):
    with st.form("client_form"):
        nom = st.text_input("Nom complet")
        email = st.text_input("Email")
        telephone = st.text_input("Téléphone")
        adresse = st.text_input("Adresse")
        ville = st.text_input("Ville")
        code_postal = st.number_input("Code Postal", min_value=0, step=1)

        submitted = st.form_submit_button("Ajouter le client")
        if submitted:
            if nom and email and telephone and adresse and ville:
                insert_client(adresse, ville, int(code_postal), email, telephone, nom)
                st.success(f"✅ Client '{nom}' ajouté avec succès !")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs.")

st.markdown("## 📅 Réservations")
reservations_df = get_reservations()
st.dataframe(reservations_df)

with st.expander("➕ Ajouter une réservation"):
    with st.form("reservation_form"):
        conn = connect_db()
        clients = pd.read_sql_query("SELECT id, nom FROM Client", conn)
        conn.close()

        client_nom = st.selectbox("Choisir un client", clients["nom"])
        client_id = clients[clients["nom"] == client_nom]["id"].values[0]

        date_debut = st.date_input("Date début")
        date_fin = st.date_input("Date fin")

        submit_resa = st.form_submit_button("Ajouter la réservation")
        if submit_resa:
            if date_debut < date_fin:
                insert_reservation(str(date_debut), str(date_fin), int(client_id))
                st.success("✅ Réservation ajoutée avec succès !")
            else:
                st.error("❌ La date de début doit être avant la date de fin.")

st.markdown("## 🔎 Recherche de chambres disponibles")
with st.form("disponibilite_form"):
    d1 = st.date_input("Date début (recherche)")
    d2 = st.date_input("Date fin (recherche)")

    submit_search = st.form_submit_button("Rechercher")
    if submit_search:
        if d1 < d2:
            disponibles_df = get_chambres_disponibles(str(d1), str(d2))
            st.success(f"{len(disponibles_df)} chambre(s) trouvée(s).")
            st.dataframe(disponibles_df)
        else:
            st.warning("⚠️ La date de début doit être avant la date de fin.")
