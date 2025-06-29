from django.db.models import Count, Sum, F, OuterRef, Exists ,Func ,IntegerField,Avg
from django.db.models import Q
from django.shortcuts import render
import json
from .models import FactTable, DimTemps, DimReponse, DimClient,CommentaireClient
from django.db.models.functions import Upper, Coalesce
from django.db.models import  Case, When, Value, CharField
from .wilaya_coords import WILAYA_COORDS
from .models import LatestResponseCsat , LatestResponseNps

from user.models import Profile
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Cast


from django.http import JsonResponse
from .models import CommentaireClient
import re
from collections import Counter



@login_required(login_url='login_user')
def home(request):
    # ========================================
    # === RÉCUPÉRATION DES PARAMÈTRES GET ===
    # ========================================
    trimestre_filter = request.GET.get('mois')         # Trimestre pour les problèmes clients
    periode = request.GET.get('mois')                    # Trimestre pour l'analyse de sentiment global
    mois_range_str = request.GET.get('mois')          # Semestre pour l'analyse de churn
    trimestre_str = request.GET.get('mois')        # Trimestre pour les top services 
    annees = list(DimTemps.objects.values_list('annee', flat=True).distinct().order_by('-annee'))    
    annee33 = request.GET.get('annee') or (str(annees[0]) if annees else '')
    # ====================================
    # === DÉFINITION DES PÉRIODES TEMPORELLES ===
    # ====================================
    trimestres = {
        '1': [1, 2, 3],
        '2': [4, 5, 6],
        '3': [7, 8, 9],
        '4': [10, 11, 12],
    }

    six_month = {
        '1': [1, 2, 3, 4, 5, 6],
        '2': [7, 8, 9, 10, 11, 12],
    }

    # ================================
    # === MAPPAGE DES LABELS NATURES ===
    # ================================
    LABELS_MAP = {
        "1": "Probléme d'Internet ",
        "2": "Qualité des appels",
        "3": "Offres et services",
        "4": "Prix et tarification",
        "5": "Service client",
        "6": "Rien de tout ça",
        "UNKNOWN": "Autre"
    }

    # ================================================
    # === IDENTIFICATION DES RÉPONSES NON EXPLOITABLES ===
    # ================================================
    reponse_ids = DimReponse.objects.filter(
        Q(nps_reponse='VIDE') | Q(nps_reponse__iexact='UNKNOWN') |
        Q(csat_reponse='VIDE') | Q(csat_reponse__iexact='UNKNOWN') |
        Q(satis_insatis='VIDE') | Q(satis_insatis__iexact='UNKNOWN') |
        Q(amelioraion_generale='VIDE') | Q(amelioraion_generale__iexact='UNKNOWN') |
        Q(amelioraion_passif='VIDE') | Q(amelioraion_passif__iexact='UNKNOWN') |
        Q(problemes='VIDE') | Q(problemes__iexact='UNKNOWN') |
        Q(amelioraion_plus='VIDE') | Q(amelioraion_plus__iexact='UNKNOWN') |
        Q(problemes_appel='VIDE') | Q(problemes_appel__iexact='UNKNOWN')
    ).values_list('id_reponse', flat=True)

    # =================================
    # === CALCUL DU TAUX DE RÉPONSE ===
    # =================================
    total = FactTable.objects.count()
    non_reponse = FactTable.objects.filter(id_reponse__in=reponse_ids).count()
    taux_reponses = ((total - non_reponse) * 100) / total

    



    # ================================================================
    # === SCORE CSAT GLOBAL (DERNIERS REPONSES DE CHAQUE CLIENT )  ===
    # ================================================================
    csat_total = LatestResponseCsat.objects.count()
    csat_1 = LatestResponseCsat.objects.filter(csat=1).count()
    csat_score = (csat_1 / csat_total) * 10 if csat_total > 0 else 0

    # =======================================================
    # === SCORE NPS (DERNIERS REPONSES DE CHAQUE CLIENT ) ===
    # =======================================================
    responses = LatestResponseNps.objects.all()
    total = responses.count()
    nps_sum = responses.aggregate(total_nps=Sum('nps'))
    total_nps_value = nps_sum['total_nps']
    nps_score = round((total_nps_value / total) * 100, 2) if total > 0 else 0



    # =============================
    # === CALCUL DU TAUX DE CHURN ===
    # =============================
    total_clients = DimClient.objects.count()
    churned_clients = DimClient.objects.filter(abonne_status__iexact="TER").count()
    churn_rate = (churned_clients / total_clients) * 100 if total_clients > 0 else 0

    # ==================================================
    # === FILTRAGE DES FACTURES POUR LE SENTIMENT GLOBAL ===
    # ==================================================
    factures = FactTable.objects.all()
    if periode in trimestres:
        mois_cibles = trimestres[periode]
        ids_temps = DimTemps.objects.filter(mois__in=mois_cibles).values_list('id_date', flat=True)
        factures = factures.filter(id_date__in=ids_temps)

    # ================================
    # === ANALYSE DU SENTIMENT GLOBAL ===
    # ================================
    commentaires_qs = CommentaireClient.objects.all()

    if periode in six_month:
        mois_cibless = six_month[periode]
        commentaires_qs = commentaires_qs.annotate(mois=ExtractMonth('survey_date'))
        commentaires_qs = commentaires_qs.filter(mois__in=mois_cibless)

    if annee33:
        try:
            annee_intt = int(annee33)
            commentaires_qs = commentaires_qs.annotate(annee=ExtractYear('survey_date'))
            commentaires_qs = commentaires_qs.filter(annee=annee_intt)
        except ValueError:
            pass

    # Comptage des sentiments
    sentiment_counts = (
        commentaires_qs
        .values('sentiment')
        .annotate(count=Count('id_client'))
    )

    # Initialisation
    nb_positifs = nb_negatifs = nb_neutres = 0

    for stat in sentiment_counts:
        sentiment = (stat['sentiment'] or '').lower()
        if sentiment == 'positif':
            nb_positifs = stat['count']
        elif sentiment in ('négatif', 'negatif'):
            nb_negatifs = stat['count']
        elif sentiment == 'neutre':
            nb_neutres = stat['count']

    sentiment_data = {
        'positif': nb_positifs,
        'neutre': nb_neutres,
        'negatif': nb_negatifs,
    }


    # ==================================
    # === LES CLIENTS A RISQUE      ===
    # ==================================
   # === Filtrage des clients 0–3 mois ===
    clients_03 = DimClient.objects.filter(age_client='0-3')

    # === Récupération des entrées détracteurs et non satisfaits pour ces clients ===
    detract_entries = FactTable.objects.filter(is_detracteur=1, id_client__in=clients_03)
    nonsatisfait_entries = FactTable.objects.filter(non_satisfait=1, id_client__in=clients_03)
    # Appliquer le filtre par année si disponible
    annee_str = request.GET.get("annee") or (str(annees[0]) if annees else '')
    if annee_str:
        try:
            annee_int = int(annee_str)
            detract_entries = detract_entries.filter(id_date__annee=annee_int)
            nonsatisfait_entries = nonsatisfait_entries.filter(id_date__annee=annee_int)
        except ValueError:
            pass  # Ignore l'entrée invalide

    # === Croisement des clients qui sont à la fois détracteurs et non satisfaits ===
    detract_pairs = set(detract_entries.values_list('id_client', 'id_date'))
    nonsatisfait_pairs = set(nonsatisfait_entries.values_list('id_client', 'id_date'))

    common_pairs = detract_pairs & nonsatisfait_pairs
    common_clients = [pair[0] for pair in common_pairs]
    common_dates = [pair[1] for pair in common_pairs]

    # === Récupération finale des entrées croisées ===
    final_results = FactTable.objects.filter(
        is_detracteur=1,
        id_client__in=common_clients,
        id_date__in=common_dates
    )
    # === Filtrage par mois si besoin ===
    final_filtered = final_results
    if mois_range_str in six_month:
        mois_range = six_month[mois_range_str]
        final_filtered = final_results.filter(id_date__mois__in=mois_range)

    # === Comptage des churns par mois ===
    churn_counts = final_filtered.values('id_date__mois').annotate(count=Count('id_date')).order_by('id_date__mois')
    churn_data = [{'mois': row['id_date__mois'], 'count': row['count']} for row in churn_counts]








    # ======================================================
    # === SERVICES POSANT PROBLÈME POUR LES DÉTRACTEURS ===
    # ======================================================

    # Récupération de l'année sélectionnée
    annee_filter = request.GET.get("annee") or (str(annees[0]) if annees else '')



    queryset = FactTable.objects.filter(
        id_question=5,
        id_reponse__satis_insatis__isnull=False
    )

    if trimestre_filter:
        mois = trimestres[trimestre_filter]  # ex : [1,2,3]
        queryset = queryset.filter(id_date__mois__in=mois)

    if annee_filter:
        annee_int = int(annee_filter)
        queryset = queryset.filter(id_date__annee=annee_int)

    response_count = (
        queryset
        .values('id_reponse__satis_insatis')
        .annotate(count=Count('id'))
        .order_by('id_reponse__satis_insatis')
    )

    LABELS_MAP = {
        "1": "Probléme d'Internet ",
        "2": "Qualité des appels",
        "3": "Offres et services",
        "4": "Prix et tarification",
        "5": "Service client",
        "6": "Rien de tout ça",
        "UNKNOWN": "Autre"
    }

    problem_labels = [
        LABELS_MAP.get(item['id_reponse__satis_insatis'], LABELS_MAP["UNKNOWN"])
        for item in response_count
    ]
    problem_counts = [item['count'] for item in response_count]














    # =====================================================
    # === SERVICES LES PLUS APPRÉCIÉS PAR LES PROMOTEURS ===
    # =====================================================
    # Récupération de l'année depuis GET
    annee_filter2 = request.GET.get("annee") or (str(annees[0]) if annees else '') 

    
    # Base de la requête
    queryset = FactTable.objects.filter(
        id_question=2,
        id_reponse__satis_insatis__isnull=False
    )

    # Appliquer le filtre de trimestre s'il est défini
    if trimestre_str:
        mois = trimestres[trimestre_str]  # ex : [1,2,3]
        queryset = queryset.filter(id_date__mois__in=mois)

    # Appliquer le filtre d'année s'il est défini
    if annee_filter2:
        annee_int = int(annee_filter2)
        queryset = queryset.filter(id_date__annee=annee_int)

    # Groupement et comptage
    response_counts = (
        queryset
        .values('id_reponse__satis_insatis')
        .annotate(count=Count('id'))
        .order_by('id_reponse__satis_insatis')
    )

    # Préparer les données pour affichage
    top_labels = [
        LABELS_MAP.get(item['id_reponse__satis_insatis'], "Autre")
        for item in response_counts
    ]
    top_counts = [item['count'] for item in response_counts]

     # Agrégation des clients par Wilaya et BU
    distribution = (
        FactTable.objects
        .values('id_region__wilaya', 'id_region__bu')
        .annotate(clients=Count('id_client', distinct=True))
    )

    # Formatage des données pour Plotly
    wilayas = []
    for item in distribution:
        wilaya = item['id_region__wilaya']
        if wilaya in WILAYA_COORDS:
            wilayas.append({
                'name': wilaya,
                'bu': item['id_region__bu'],
                'clients': item['clients'],
                'lat': WILAYA_COORDS[wilaya]['lat'],
                'lon': WILAYA_COORDS[wilaya]['lon']
            })

    # =============================
    # === ENVOI DES DONNÉES À LA VUE ===
    # =============================
    context = {
        'nps_score': round(nps_score, 2),
        'csat_score': round(csat_score, 2),
        'churn_rate': round(churn_rate, 2),
        'taux_reponses': round(taux_reponses, 2),
        'sentiment_data_json': json.dumps(list(sentiment_data.values())),
        'churn_data_json': json.dumps(churn_data),
        'problem_labels': json.dumps(problem_labels),
        'problem_counts': json.dumps(problem_counts),
        'top_labels': json.dumps(top_labels),
        'top_counts': json.dumps(top_counts),
        'selected_trimestre': trimestre_filter,
        'selected_periode': periode,
        'selected_mois_range': mois_range_str,
        'selected_trimestre_top': trimestre_str,
        'annees': annees,
        'wilayas': wilayas,
    }

    return render(request, 'home.html', context)


@login_required(login_url='login_user')
def satisfaction(request):
    annees = list(DimTemps.objects.values_list('annee', flat=True).distinct().order_by('-annee'))    

    # ================================
    # === RÉCUPÉRATION DES FILTRES ===
    # ================================
    evolution = request.GET.get('evolution')  # Semestre pour le graphe csat
    evolution_profil = request.GET.get('evolution_profil')  # Semestre pour le graphe nps
    
    # =======================================
    # === MAPPAGE DES LABELS DE RÉPONSES ===
    # =======================================
    six_month = {
        '1': [1, 2, 3, 4, 5, 6],
        '2': [7, 8, 9, 10, 11, 12],
    }

    # =============================
    # === CALCUL DU SCORE CSAT ====
    # =============================

    csat_total = LatestResponseCsat.objects.count()
    csat_1 = LatestResponseCsat.objects.filter(csat=1).count()
    csat_0 = LatestResponseCsat.objects.filter(non_satisfait=1).count()

    csat_score = (csat_1 / csat_total) * 10 if csat_total > 0 else 0
    satisfaits = (csat_1 / csat_total) * 100 if csat_total > 0 else 0
    insatisfaits = (csat_0 / csat_total) * 100 if csat_total > 0 else 0
    # =============================
    # === CSAT  1              ===
    # =============================

    annee_filter = request.GET.get("année") or (str(annees[0]) if annees else '') 
    if evolution in six_month:
        mois_cibles = six_month[evolution]
        filtered_queryset = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            csat=1,
            id_date__mois__in=mois_cibles,
            id_date__date__isnull=False
        )
    else:
        filtered_queryset = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            csat=1,
            id_date__date__isnull=False
        )

    # Ajouter le filtre année
    if annee_filter:
        try:
            annee_int = int(annee_filter)
            filtered_queryset = filtered_queryset.filter(id_date__annee=annee_int)
        except ValueError:
            pass

    # Annoter
    all_responses = FactTable.objects.annotate(
        match_csat=Exists(filtered_queryset)
    ).filter(match_csat=True)

    response_count = (
        all_responses
        .select_related('id_date')
        .values(label=F('id_date__mois'))
        .annotate(count=Count('id_client', distinct=True))
    )

    mois_labels = [item['label'] for item in response_count]
    Promoteur_counts = [item['count'] for item in response_count]
    # =============================
    # === CSAT  0              ===
    # =============================

    if evolution in six_month:
        mois_cibles = six_month[evolution]
        filtered_queryset_csat0 = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            non_satisfait=1,
            id_date__mois__in=mois_cibles,
            id_date__date__isnull=False
        )
    else:
        filtered_queryset_csat0 = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            non_satisfait=1,
            id_date__date__isnull=False
        )

    # Ajouter le filtre année
    if annee_filter:
        try:
            annee_int = int(annee_filter)
            filtered_queryset_csat0 = filtered_queryset_csat0.filter(id_date__annee=annee_int)
        except ValueError:
            pass

    # Annoter
    all_responses = FactTable.objects.annotate(
        match_csat=Exists(filtered_queryset_csat0)
    ).filter(match_csat=True)

    response_count = (
        all_responses
        .select_related('id_date')
        .values(label=F('id_date__mois'))
        .annotate(count=Count('id_client', distinct=True))
    )

    mois_labels = [item['label'] for item in response_count]
    insatisafait_counts = [item['count'] for item in response_count]


    # =============================
    # === CSAT  AGE             ===
    # =============================

    # Tranches d'âge attendues dans un ordre précis
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']

    # Satisfaits (csat = 1)
    satisfaits_raw = (
        LatestResponseCsat.objects
        .filter(csat=1, id_client__age_abonne__isnull=False)
        .values('id_client__age_abonne')
        .annotate(count=Count('id_client'))
    )

    # Non satisfaits (non_satisfait = 1)
    non_satisfaits_raw = (
        LatestResponseCsat.objects
        .filter(non_satisfait=1, id_client__age_abonne__isnull=False)
        .values('id_client__age_abonne')
        .annotate(count=Count('id_client'))
    )

    # Mapping {tranche: count}
    satisfaits_dict = {item['id_client__age_abonne']: item['count'] for item in satisfaits_raw}
    non_satisfaits_dict = {item['id_client__age_abonne']: item['count'] for item in non_satisfaits_raw}

    # Construction des listes finales alignées avec l'ordre
    age_labels = age_ranges
    satisfaits_counts = [satisfaits_dict.get(age, 0) for age in age_ranges]
    non_satisfaits_counts = [non_satisfaits_dict.get(age, 0) for age in age_ranges]


    # =============================
    # === CALCUL DU SCORE NPS ====
    # =============================
    responses = LatestResponseNps.objects.all()
    total = responses.count()

    # ==============================================================
    # === CALCUL DU TAUX DES DÉTRACTEURS, PROMOTEURS, PASSIFS   ====
    # ==============================================================
    
    
    promoteurs = responses.filter(is_promoteur=1).count()
    detracteurs = responses.filter(is_detracteur=1).count()
    passifs = responses.filter(is_passif=1).count()

    pourcentage_promoteurs = round((promoteurs / total) * 100, 2) if total > 0 else 0
    pourcentage_detracteurs = round((detracteurs / total) * 100, 2) if total > 0 else 0
    pourcentage_passifs = round((passifs / total) * 100, 2) if total > 0 else 0



    nps_sum = responses.aggregate(total_nps=Sum('nps'))
    total_nps_value = nps_sum['total_nps'] if nps_sum['total_nps'] is not None else 0

    nps_score = round((total_nps_value / total) * 100, 2) if total > 0 else 0

    
    # ==================================
    # === Évolution des Profils NPS ====
    # ==================================
    annee_filter = request.GET.get("année") or (str(annees[0]) if annees else '') 


    if evolution_profil in six_month:
        mois_filtrés = six_month[evolution_profil]

        # Sous-requêtes par profil
        sous_requete_nps_promoteurs = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            nps=1,
            id_date__mois__in=mois_filtrés,
            id_date__date__isnull=False
        )
        sous_requete_nps_detracteurs = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            is_detracteur=1,
            id_date__mois__in=mois_filtrés,
            id_date__date__isnull=False
        )
        sous_requete_nps_passif = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            is_passif=1,
            id_date__mois__in=mois_filtrés,
            id_date__date__isnull=False
        )
    else:
        sous_requete_nps_promoteurs = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            nps=1,
            id_date__date__isnull=False
        )
        sous_requete_nps_detracteurs = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            is_detracteur=1,
            id_date__date__isnull=False
        )
        sous_requete_nps_passif = FactTable.objects.filter(
            id_client=OuterRef('id_client'),
            id_date=OuterRef('id_date'),
            is_passif=1,
            id_date__date__isnull=False
        )
    # Ajouter le filtre d'année à chaque sous-requête
    if annee_filter:
        try:
            annee_int = int(annee_filter)
            sous_requete_nps_promoteurs = sous_requete_nps_promoteurs.filter(id_date__annee=annee_int)
            sous_requete_nps_detracteurs = sous_requete_nps_detracteurs.filter(id_date__annee=annee_int)
            sous_requete_nps_passif = sous_requete_nps_passif.filter(id_date__annee=annee_int)
        except ValueError:
            pass  # Ignore les valeurs invalides
        
    # === PROMOTEURS ===
    factures_promoteurs = FactTable.objects.annotate(
        est_promoteur=Exists(sous_requete_nps_promoteurs)
    ).filter(est_promoteur=True)

    nps_promoteurs_par_mois = (
        factures_promoteurs
        .values(label=F('id_date__mois'))
        .annotate(nb_clients=Count('id_client', distinct=True))
        .order_by('label')
    )

    # === DÉTRACTEURS ===
    factures_detracteurs = FactTable.objects.annotate(
        est_detracteur=Exists(sous_requete_nps_detracteurs)
    ).filter(est_detracteur=True)

    nps_detracteurs_par_mois = (
        factures_detracteurs
        .values(label=F('id_date__mois'))
        .annotate(nb_clients=Count('id_client', distinct=True))
        .order_by('label')
    )

    # === PASSIFS ===
    factures_passifs = FactTable.objects.annotate(
        est_passif=Exists(sous_requete_nps_passif)
    ).filter(est_passif=True)

    nps_passifs_par_mois = (
        factures_passifs
        .values(label=F('id_date__mois'))
        .annotate(nb_clients=Count('id_client', distinct=True))
        .order_by('label')
    )

    # === EXTRACTION DES LISTES ===
    liste_mois = [item['label'] for item in nps_promoteurs_par_mois]
    nombre_promoteurs = [item['nb_clients'] for item in nps_promoteurs_par_mois]
    nombre_detracteurs = [item['nb_clients'] for item in nps_detracteurs_par_mois]
    nombre_passifs = [item['nb_clients'] for item in nps_passifs_par_mois]



    # Répartition NPS par BU (sans filtre de mois)
    base_queryset = LatestResponseNps.objects.exclude(id_region__bu__iexact="Other")

    # Promoteurs
    nps_promoteurs_par_bu = (
        base_queryset.filter(is_promoteur=1)
        .values(label=F('id_region__bu'))
        .annotate(nb_clients=Count('id_client', distinct=True))
        .order_by('label')
    )

    # Détracteurs
    nps_detracteurs_par_bu = (
        base_queryset.filter(is_detracteur=1)
        .values(label=F('id_region__bu'))
        .annotate(nb_clients=Count('id_client', distinct=True))
        .order_by('label')
    )

    # Passifs
    nps_passifs_par_bu = (
        base_queryset.filter(is_passif=1)
        .values(label=F('id_region__bu'))
        .annotate(nb_clients=Count('id_client', distinct=True))
        .order_by('label')
    )

    # Extraction pour le frontend
    liste_bu = [item['label'] for item in nps_promoteurs_par_bu]
    nombre_promoteurss = [item['nb_clients'] for item in nps_promoteurs_par_bu]
    nombre_detracteurss = [item['nb_clients'] for item in nps_detracteurs_par_bu]
    nombre_passifss = [item['nb_clients'] for item in nps_passifs_par_bu]

    context = {
        'satisfaits': round(satisfaits, 2),
        'insatisfaits': round(insatisfaits, 2),
        'csat_score': round(csat_score, 2),

        'nps_score': round(nps_score, 2),
        'pourcentage_promoteurs': round(pourcentage_promoteurs, 2),
        'pourcentage_detracteurs': round(pourcentage_detracteurs, 2),
        'pourcentage_passifs': round(pourcentage_passifs, 2),
        
        'mois_labels': json.dumps(mois_labels),
        'Promoteur_counts': json.dumps(Promoteur_counts),
        'insatisafait_counts': json.dumps(insatisafait_counts),
        'age_labels': json.dumps(age_labels),
        'age_counts': json.dumps(satisfaits_counts),
        'age1_counts': json.dumps(non_satisfaits_counts ),
        'liste_mois': json.dumps(liste_mois),
        'nombre_promoteurs': json.dumps(nombre_promoteurs),
        'nombre_detracteurs': json.dumps(nombre_detracteurs),
        'nombre_passifs': json.dumps(nombre_passifs),
        'liste_bu': json.dumps(liste_bu),
        'nombre_promoteurss': json.dumps(nombre_promoteurss),
        'nombre_detracteurss': json.dumps(nombre_detracteurss),
        'nombre_passifss': json.dumps(nombre_passifss),
        'annees': annees,

    }

    return render(request, 'satisfaction.html', context)












@login_required(login_url='login_user')
def clients(request):
    total_clients = DimClient.objects.count()
    clients_termines = DimClient.objects.filter(abonne_status='TER').count()
    clients_actifs = DimClient.objects.filter(abonne_status='ACT').count()

    #  Répartition par tranche d'âge (age_abonne)
    AGE_ABONNE_ORDER = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']

    age_abonne_grouped = (
        DimClient.objects
        .values('age_abonne')
        .annotate(count=Count('id_client'))
    )

    # On ne touche pas aux valeurs nulles ici : on garde uniquement ce qui correspond à AGE_ABONNE_ORDER
    age_abonne_counts_dict = {
        item['age_abonne']: item['count']
        for item in age_abonne_grouped
        if item['age_abonne'] in AGE_ABONNE_ORDER
    }

    # Création des listes dans l’ordre voulu
    age_abonne_labels = []
    age_abonne_counts = []

    for tranche in AGE_ABONNE_ORDER:
        age_abonne_labels.append(tranche)
        age_abonne_counts.append(age_abonne_counts_dict.get(tranche, 0))






    # Répartition par ancienneté (age_client)
    AGE_CLIENT_ORDER =['0-3', '4-8', '9-12', '13-20', '20+', 'Unknown']
    age_client_grouped = (
        DimClient.objects
        .values('age_client')
        .annotate(count=Count('id_client'))
    )
    age_client_counts_dict = {
        (item['age_client'] or 'Inconnu'): item['count']
        for item in age_client_grouped
    }
    age_client_labels = []
    age_client_counts = []
    for tranche in AGE_CLIENT_ORDER:
        age_client_labels.append(tranche)
        age_client_counts.append(age_client_counts_dict.get(tranche, 0))

    #  Répartition par type de client
    type_grouped = (
        DimClient.objects
        .annotate(type_normalized=Upper(Coalesce('type_client', Value('Inconnu'))))
        .values('type_normalized')
        .annotate(count=Count('id_client'))
        .order_by('-count')
    )
    type_labels = [item['type_normalized'] for item in type_grouped]
    type_counts = [item['count'] for item in type_grouped]

    #  Répartition par type de souscription (type_abonne)
    souscription_grouped = (
        DimClient.objects
        .annotate(souscription_normalized=Upper(Coalesce('type_abonne', Value('Inconnu'))))
        .values('souscription_normalized')
        .annotate(count=Count('id_client'))
        .order_by('-count')
    )
    souscription_labels = [item['souscription_normalized'] for item in souscription_grouped]
    souscription_counts = [item['count'] for item in souscription_grouped]

     # Liste des offres spécifiques à surveiller
    target_offers = [
        'Newhaylabezzef', 'DJEZZY_HAYLABEZZEF', 'Lowvalue',
        'Mixteprepaid', 'DJEZZY_HAYLAMAXI', 'DjezzyCarte_NEW',
        'Offrejeune', 'Hadraprepaid', 'Individual Hybrid'
    ]

    # Annoter les clients avec "offer_group"
    clients = DimClient.objects.annotate(
        offer_group=Case(
            *[When(globale_profile=offer, then=Value(offer)) for offer in target_offers],
            default=Value('Other'),
            output_field=CharField()
        )
    )

    # Compter le nombre de clients par groupe d'offre
    offer_counts = clients.values('offer_group').annotate(count=Count('id_client'))

    # Extraire les labels et les counts
    labels = [item['offer_group'] for item in offer_counts]
    counts = [item['count'] for item in offer_counts]



    # Agrégation des clients par Wilaya et BU
    distribution = (
        FactTable.objects
        .values('id_region__wilaya', 'id_region__bu')
        .annotate(clients=Count('id_client', distinct=True))
    )

    # Formatage des données pour Plotly
    wilayas = []
    for item in distribution:
        wilaya = item['id_region__wilaya']
        if wilaya in WILAYA_COORDS:
            wilayas.append({
                'name': wilaya,
                'bu': item['id_region__bu'],
                'clients': item['clients'],
                'lat': WILAYA_COORDS[wilaya]['lat'],
                'lon': WILAYA_COORDS[wilaya]['lon']
            })




    context = {
        'total_clients': total_clients,
        'clients_termines': clients_termines,
        'clients_actifs': clients_actifs,
        'age_abonne_labels': age_abonne_labels,
        'age_abonne_counts': age_abonne_counts,
        'age_client_labels': age_client_labels,
        'age_client_counts': age_client_counts,
        'type_labels': type_labels,
        'type_counts': type_counts,
        'souscription_labels': souscription_labels,
        'souscription_counts': souscription_counts,
        'labels': labels,
        'counts': counts,
        'wilayas': wilayas,
        
    }

    return render(request, 'clients.html', context)


# Fonctions pour extraire le mois et l'année depuis une colonne de type date
class ExtractMonth(Func):
    function = 'EXTRACT'
    template = "%(function)s(MONTH FROM %(expressions)s)"
    output_field = IntegerField()

class ExtractYear(Func):
    function = 'EXTRACT'
    template = "%(function)s(YEAR FROM %(expressions)s)"
    output_field = IntegerField()















































@login_required(login_url='login_user')
def export(request):
    # Logic for the export page
    return HttpResponse("Export functionality will be implemented here.")