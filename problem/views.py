from django.shortcuts import render
from satisfaction_client.models import FactTable ,DimTemps
from django.db.models import Count, F
from django.db.models import Count, Case, When, Value, CharField


def problem_internet(request):
    
    # ====================================================
    # === PARAMÈTRES ET FILTRES DE LA REQUÊTE GET      ===
    # ====================================================

    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee)
    filtre1 = request.GET.get("mois")
    
    # =======================================================
    # === TOTAL DES PROBLÈMES TOUTES QUESTIONS CONFONDUES ===
    # =======================================================
    # Problèmes liés aux questions 9, 12, 14
    totalProblems1 = FactTable.objects.filter(
        id_question__in=[9, 12, 14],
        id_date__annee=annee_int  # filtre année
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )

    if filtre1 == '1':
        totalProblems1 = totalProblems1.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems1 = totalProblems1.filter(id_date__mois__gte=7)

    totalProblems1 = totalProblems1.count()

    # Problèmes liés à la question 4
    totalProblems2 = FactTable.objects.filter(
        id_question=4,
        id_date__annee=annee_int  # filtre année
    ).exclude(
        id_reponse__problemes_appel__isnull=True
    ).exclude(
        id_reponse__problemes_appel=""
    ).exclude(
        id_reponse__problemes_appel="VIDE"
    ).exclude(
        id_reponse__problemes_appel="UNKNOWN"
    )

    if filtre1 == '1':
        totalProblems2 = totalProblems2.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems2 = totalProblems2.filter(id_date__mois__gte=7)

    totalProblems2 = totalProblems2.count()

    totalProblems = totalProblems1 + totalProblems2

    # ====================================================
    # === TOTAL DES PROBLÈMES INTERNET (question 6)     ===
    # ====================================================
    totalProblemsInternet = FactTable.objects.filter(
        id_question=6,
        id_date__annee=annee_int  # filtre année
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )

    if filtre1 == '1':
        totalProblemsInternet = totalProblemsInternet.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblemsInternet = totalProblemsInternet.filter(id_date__mois__gte=7)

    totalProblemsInternet = totalProblemsInternet.count()

    # ====================================================
    # === ÉTAPE 1 : Filtrage des réponses valides       ===
    # ====================================================
    filtered_question = FactTable.objects.filter(
        id_question=6,
        id_date__annee=annee_int  # filtre année
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )

    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)

    filtered_question_count = filtered_question.count()

    # ====================================================
    # === ÉTAPE 2 : Comptage par type de problème       ===
    # ====================================================
    response_count = filtered_question.values(
        'id_reponse__problemes'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__problemes']: item['count']
        for item in response_count
    }

    # Calcul des pourcentages
    VitesseInternet = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    CoupureInternet = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    NonReseau = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    FaibleReseau = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # ====================================================
    # === ÉVOLUTION MENSUELLE DES 4 PROBLÈMES INTERNET  ===
    # ====================================================
    PROBLEMES_CODES = ["1", "2", "3", "4"]
    base_query = FactTable.objects.filter(id_question=6, id_reponse__problemes__in=PROBLEMES_CODES)

    # === Application des filtres année et période (mois) ===
    
    base_query = base_query.filter(id_date__annee=annee_int)
       

    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    # === Requêtes groupées par mois et type de problème ===
    qs_p1 = base_query.filter(id_reponse__problemes="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__problemes="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__problemes="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__problemes="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

    # === Construction de la liste des mois présents ===
    mois_set = set()
    for qs in [qs_p1, qs_p2, qs_p3, qs_p4]:
        for item in qs:
            mois_set.add(f"{item['label']:02d}")
    liste_mois = sorted(mois_set)

    # === Construction des dictionnaires {mois: valeur} ===
    def qs_to_dict(qs):
        return {f"{item['label']:02d}": item['nb_clients'] for item in qs}

    dict_p1 = qs_to_dict(qs_p1)
    dict_p2 = qs_to_dict(qs_p2)
    dict_p3 = qs_to_dict(qs_p3)
    dict_p4 = qs_to_dict(qs_p4)

    # === Conversion en listes alignées ===
    def build_count_list(d):
        return [d.get(mois, 0) for mois in liste_mois]

    nombre_p1 = build_count_list(dict_p1)
    nombre_p2 = build_count_list(dict_p2)
    nombre_p3 = build_count_list(dict_p3)
    nombre_p4 = build_count_list(dict_p4)

    # ====================================================
    # === RÉPARTITION DES PROBLÈMES PAR BU              ===
    # ====================================================
    base_queryset = FactTable.objects.filter(id_question=6).exclude(id_region__bu="Other")

    base_queryset = base_queryset.filter(id_date__annee=annee_int)
        

    
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)
    
    
    
    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts = []
    probleme2_counts = []
    probleme3_counts = []
    probleme4_counts = []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        probleme1_counts.append(bu_queryset.filter(id_reponse__problemes="1").count())
        probleme2_counts.append(bu_queryset.filter(id_reponse__problemes="2").count())
        probleme3_counts.append(bu_queryset.filter(id_reponse__problemes="3").count())
        probleme4_counts.append(bu_queryset.filter(id_reponse__problemes="4").count())
        bu_list.append(bu)

    # ====================================================
    # === RÉPARTITION PAR TRANCHE D’ÂGE                ===
    # ====================================================
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    probleme_ids = ["1", "2", "3", "4", "5"]

    data_probleme_1 = [0] * len(age_ranges)
    data_probleme_2 = [0] * len(age_ranges)
    data_probleme_3 = [0] * len(age_ranges)
    data_probleme_4 = [0] * len(age_ranges)
    data_probleme_5 = [0] * len(age_ranges)

    toutes_les_listes = [data_probleme_1, data_probleme_2, data_probleme_3, data_probleme_4, data_probleme_5]

    for i, probleme_id in enumerate(probleme_ids):
        reponses = FactTable.objects.filter(
            id_question=6,
            id_reponse__problemes=probleme_id,
            id_date__annee=annee_int  # applique le filtre année
        )
        if filtre1 == '1':
            reponses = reponses.filter(id_date__mois__lte=6)
        elif filtre1 == '2':
            reponses = reponses.filter(id_date__mois__gte=7)
        comptage = reponses.values('id_client__age_abonne').annotate(count=Count('id'))

        age_counts = {}
        for r in comptage:
            age = r['id_client__age_abonne'] or 'Unknown'
            age_counts[age] = r['count']

        for j, tranche in enumerate(age_ranges):
            toutes_les_listes[i][j] = age_counts.get(tranche, 0)

    # ====================================================
    # === RÉPARTITION PAR TYPE DE TÉLÉPHONE            ===
    # ====================================================
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']

    count_probleme_1 = [0] * len(ordered_type_tel)
    count_probleme_2 = [0] * len(ordered_type_tel)
    count_probleme_3 = [0] * len(ordered_type_tel)
    count_probleme_4 = [0] * len(ordered_type_tel)

    queryset = FactTable.objects.filter(id_question=6)
    queryset = queryset.filter(id_date__annee=annee_int)

    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)






    aggregation = queryset.values('id_client__type_tel', 'id_reponse__problemes').annotate(total=Count('id'))

    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__problemes']
        count = item['total']

        if tel_type in type_tel_order:
            idx = type_tel_order.index(tel_type)
        else:
            idx = len(type_tel_order)  # index pour "Other"

        if probleme_type == '1':
            count_probleme_1[idx] += count
        elif probleme_type == '2':
            count_probleme_2[idx] += count
        elif probleme_type == '3':
            count_probleme_3[idx] += count
        elif probleme_type == '4':
            count_probleme_4[idx] += count

    # ====================================================
    # === CONTEXTE À ENVOYER AU TEMPLATE                ===
    # ====================================================
    context = {
        'totalProblemsInternet': totalProblemsInternet,
        'totalProblems': totalProblems,
        'VitesseInternet': round(VitesseInternet, 2),
        'CoupureInternet': round(CoupureInternet, 2),
        'NonReseau': round(NonReseau, 2),
        'FaibleReseau': round(FaibleReseau, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'annees': annees,
        'bu_list': bu_list,
        'probleme1_counts': probleme1_counts,
        'probleme2_counts': probleme2_counts,
        'probleme3_counts': probleme3_counts,
        'probleme4_counts': probleme4_counts,
        'age_ranges': age_ranges,
        'data_probleme_1': data_probleme_1,
        'data_probleme_2': data_probleme_2,
        'data_probleme_3': data_probleme_3,
        'data_probleme_4': data_probleme_4,
        'count_probleme_1': count_probleme_1,
        'count_probleme_2': count_probleme_2,
        'count_probleme_3': count_probleme_3,
        'count_probleme_4': count_probleme_4,

        'annee_selectionnee': annee_selectionnee,
    }

    return render(request, 'internet.html', context)


def problem_appel(request):
    # ========================== PARAMÈTRES ET FILTRES ==========================
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # ============================================
    # === Nombre total de problèmes généraux ===
    # ============================================
    totalProblems = FactTable.objects.filter(
        id_question__in=[6, 9, 12, 14]
    ).filter(
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )

    if filtre1 == '1':
        totalProblems = totalProblems.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems = totalProblems.filter(id_date__mois__gte=7)
    totalProblems = totalProblems.count()

    # =================================================
    # === Nombre total de problèmes d’appel (id=4) ===
    # =================================================
    totalProblemsappel = FactTable.objects.filter(
        id_question=4,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes_appel__isnull=True
    ).exclude(
        id_reponse__problemes_appel=""
    ).exclude(
        id_reponse__problemes_appel="VIDE"
    ).exclude(
        id_reponse__problemes_appel="UNKNOWN"
    )

    if filtre1 == '1':
        totalProblemsappel = totalProblemsappel.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblemsappel = totalProblemsappel.filter(id_date__mois__gte=7)
    totalProblemsappel = totalProblemsappel.count()

    # =======================================================================
    # === Étape 1 : Filtrer toutes les réponses valides pour id_question=4 ===
    # =======================================================================
    filtered_question = FactTable.objects.filter(
        id_question=4,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes_appel__isnull=True
    ).exclude(
        id_reponse__problemes_appel=""
    ).exclude(
        id_reponse__problemes_appel="VIDE"
    ).exclude(
        id_reponse__problemes_appel="UNKNOWN"
    )

    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question_count = filtered_question.count()

    # ====================================================
    # === Étape 2 : Compter le nombre de réponses par code problème ===
    # ====================================================
    response_count = filtered_question.values(
        'id_reponse__problemes_appel'
    ).annotate(
        count=Count('id')
    )

    # ====================================================
    # === Étape 3 : Transformer le queryset en dictionnaire ===
    # ====================================================
    response_dict = {
        item['id_reponse__problemes_appel']: item['count']
        for item in response_count
    }

    # ====================================================
    # === Étape 4 : Calculer les pourcentages des 4 problèmes ===
    # ====================================================
    ReseauFaible = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    AppelInterrompus = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    QualiteFaible = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PAppelEchoue = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # ===============================================
    # === Requête de base pour les graphiques mensuels ===
    # ===============================================
    PROBLEMES_CODES = ["1", "2", "3", "4"]
    base_query = FactTable.objects.filter(
        id_question=4,
        id_reponse__problemes_appel__in=PROBLEMES_CODES,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__problemes_appel="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__problemes_appel="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__problemes_appel="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__problemes_appel="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

    mois_set = set()
    for qs in [qs_p1, qs_p2, qs_p3, qs_p4]:
        for item in qs:
            mois_set.add(f"{item['label']:02d}")
    liste_mois = sorted(mois_set)

    def qs_to_dict(qs):
        return {f"{item['label']:02d}": item['nb_clients'] for item in qs}

    dict_p1 = qs_to_dict(qs_p1)
    dict_p2 = qs_to_dict(qs_p2)
    dict_p3 = qs_to_dict(qs_p3)
    dict_p4 = qs_to_dict(qs_p4)

    def build_count_list(d):
        return [d.get(mois, 0) for mois in liste_mois]

    nombre_p1 = build_count_list(dict_p1)
    nombre_p2 = build_count_list(dict_p2)
    nombre_p3 = build_count_list(dict_p3)
    nombre_p4 = build_count_list(dict_p4)

    # ===========================================
    # === Répartition des problèmes par BU ===
    # ===========================================
    base_queryset = FactTable.objects.filter(id_question=4, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)

    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts = []
    probleme2_counts = []
    probleme3_counts = []
    probleme4_counts = []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        p1 = bu_queryset.filter(id_reponse__problemes_appel="1").count()
        p2 = bu_queryset.filter(id_reponse__problemes_appel="2").count()
        p3 = bu_queryset.filter(id_reponse__problemes_appel="3").count()
        p4 = bu_queryset.filter(id_reponse__problemes_appel="4").count()
        bu_list.append(bu)
        probleme1_counts.append(p1)
        probleme2_counts.append(p2)
        probleme3_counts.append(p3)
        probleme4_counts.append(p4)

    # ===================================================
    # === Répartition des problèmes par tranche d’âge ===
    # ===================================================
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    probleme_ids = ["1", "2", "3", "4"]
    data_probleme_1 = [0] * len(age_ranges)
    data_probleme_2 = [0] * len(age_ranges)
    data_probleme_3 = [0] * len(age_ranges)
    data_probleme_4 = [0] * len(age_ranges)
    toutes_les_listes = [data_probleme_1, data_probleme_2, data_probleme_3, data_probleme_4]

    for i, probleme_id in enumerate(probleme_ids):
        reponses = FactTable.objects.filter(
            id_question=4,
            id_reponse__problemes_appel=probleme_id,
            id_date__annee=annee_int
        )
        if filtre1 == '1':
            reponses = reponses.filter(id_date__mois__lte=6)
        elif filtre1 == '2':
            reponses = reponses.filter(id_date__mois__gte=7)
        comptage = reponses.values('id_client__age_abonne').annotate(count=Count('id'))
        age_counts = {r['id_client__age_abonne'] or 'Unknown': r['count'] for r in comptage}
        for j, tranche in enumerate(age_ranges):
            toutes_les_listes[i][j] = age_counts.get(tranche, 0)

    # ======================================================
    # === Répartition des problèmes par type de téléphone ===
    # ======================================================
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']
    count_probleme_1 = [0] * len(ordered_type_tel)
    count_probleme_2 = [0] * len(ordered_type_tel)
    count_probleme_3 = [0] * len(ordered_type_tel)
    count_probleme_4 = [0] * len(ordered_type_tel)

    queryset = FactTable.objects.filter(id_question=4, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values('id_client__type_tel', 'id_reponse__problemes_appel').annotate(total=Count('id')).order_by()

    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__problemes_appel']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_probleme_1[idx] += count
        elif probleme_type == '2':
            count_probleme_2[idx] += count
        elif probleme_type == '3':
            count_probleme_3[idx] += count
        elif probleme_type == '4':
            count_probleme_4[idx] += count

    # ==============================
    # === Envoi des données au template ===
    # ==============================
    context = {
        'totalProblemsappel': totalProblemsappel,
        'totalProblems': totalProblems,
        'ReseauFaible': round(ReseauFaible, 2),
        'AppelInterrompus': round(AppelInterrompus, 2),
        'QualiteFaible': round(QualiteFaible, 2),
        'PAppelEchoue': round(PAppelEchoue, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'probleme1_counts': probleme1_counts,
        'probleme2_counts': probleme2_counts,
        'probleme3_counts': probleme3_counts,
        'probleme4_counts': probleme4_counts,
        'age_ranges': age_ranges,
        'data_probleme_1': data_probleme_1,
        'data_probleme_2': data_probleme_2,
        'data_probleme_3': data_probleme_3,
        'data_probleme_4': data_probleme_4,
        'count_probleme_1': count_probleme_1,
        'count_probleme_2': count_probleme_2,
        'count_probleme_3': count_probleme_3,
        'count_probleme_4': count_probleme_4,
    }

    return render(request, 'appel.html', context)




def problem_offre(request):
    # ============================================
    # 1. Récupération des paramètres de filtre (comme Internet)
    # ============================================
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # ============================================
    # 2. Calcul du nombre total de problèmes clients
    # ============================================

    # Problèmes pour les questions 6, 12, 14
    totalProblems1 = FactTable.objects.filter(
        id_question__in=[6, 12, 14],
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblems1 = totalProblems1.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems1 = totalProblems1.filter(id_date__mois__gte=7)
    totalProblems1 = totalProblems1.count()

    # Problèmes pour la question 4
    totalProblems2 = FactTable.objects.filter(
        id_question=4,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes_appel__isnull=True
    ).exclude(
        id_reponse__problemes_appel=""
    ).exclude(
        id_reponse__problemes_appel="VIDE"
    ).exclude(
        id_reponse__problemes_appel="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblems2 = totalProblems2.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems2 = totalProblems2.filter(id_date__mois__gte=7)
    totalProblems2 = totalProblems2.count()

    # Total global des problèmes
    totalProblems = totalProblems1 + totalProblems2

    # ============================================
    # 3. Analyse des problèmes liés à l'offre (question 9)
    # ============================================
    totalProblemOffre = FactTable.objects.filter(
        id_question=9,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblemOffre = totalProblemOffre.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblemOffre = totalProblemOffre.filter(id_date__mois__gte=7)
    totalProblemOffre = totalProblemOffre.count()

    filtered_question = FactTable.objects.filter(
        id_question=9,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question_count = filtered_question.count()

    # Comptage des réponses par type de problème
    response_count = filtered_question.values(
        'id_reponse__problemes'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__problemes']: item['count']
        for item in response_count
    }

    # Calcul des pourcentages
    InternetLimite = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    DataViteEpuisee = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    ValiditeCourte = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    OffreFloue = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    ChangementNonPossible = (response_dict.get("5", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # ============================================
    # 4. Évolution mensuelle des problèmes par type
    # ============================================
    PROBLEMES_CODES = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=9,
        id_reponse__problemes__in=PROBLEMES_CODES,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__problemes="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__problemes="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__problemes="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__problemes="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__problemes="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

    mois_set = set()
    for qs in [qs_p1, qs_p2, qs_p3, qs_p4, qs_p5]:
        for item in qs:
            mois_set.add(f"{item['label']:02d}")
    liste_mois = sorted(mois_set)

    def qs_to_dict(qs):
        return {f"{item['label']:02d}": item['nb_clients'] for item in qs}

    dict_p1 = qs_to_dict(qs_p1)
    dict_p2 = qs_to_dict(qs_p2)
    dict_p3 = qs_to_dict(qs_p3)
    dict_p4 = qs_to_dict(qs_p4)
    dict_p5 = qs_to_dict(qs_p5)

    def build_count_list(d):
        return [d.get(mois, 0) for mois in liste_mois]

    nombre_p1 = build_count_list(dict_p1)
    nombre_p2 = build_count_list(dict_p2)
    nombre_p3 = build_count_list(dict_p3)
    nombre_p4 = build_count_list(dict_p4)
    nombre_p5 = build_count_list(dict_p5)

    # ============================================
    # 5. Répartition des problèmes par BU
    # ============================================
    base_queryset = FactTable.objects.filter(id_question=9, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)

    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts, probleme2_counts, probleme3_counts, probleme4_counts, probleme5_counts = [], [], [], [], []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        probleme1_counts.append(bu_queryset.filter(id_reponse__problemes="1").count())
        probleme2_counts.append(bu_queryset.filter(id_reponse__problemes="2").count())
        probleme3_counts.append(bu_queryset.filter(id_reponse__problemes="3").count())
        probleme4_counts.append(bu_queryset.filter(id_reponse__problemes="4").count())
        probleme5_counts.append(bu_queryset.filter(id_reponse__problemes="5").count())
        bu_list.append(bu)

    # ============================================
    # 6. Répartition des problèmes par tranche d'âge
    # ============================================
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    probleme_ids = ["1", "2", "3", "4", "5"]

    data_probleme_1 = [0] * len(age_ranges)
    data_probleme_2 = [0] * len(age_ranges)
    data_probleme_3 = [0] * len(age_ranges)
    data_probleme_4 = [0] * len(age_ranges)
    data_probleme_5 = [0] * len(age_ranges)

    toutes_les_listes = [data_probleme_1, data_probleme_2, data_probleme_3, data_probleme_4, data_probleme_5]

    for i, probleme_id in enumerate(probleme_ids):
        reponses = FactTable.objects.filter(
            id_question=9,
            id_reponse__problemes=probleme_id,
            id_date__annee=annee_int
        )
        if filtre1 == '1':
            reponses = reponses.filter(id_date__mois__lte=6)
        elif filtre1 == '2':
            reponses = reponses.filter(id_date__mois__gte=7)
        comptage = reponses.values('id_client__age_abonne').annotate(count=Count('id'))
        age_counts = {r['id_client__age_abonne'] or 'Unknown': r['count'] for r in comptage}
        for j, tranche in enumerate(age_ranges):
            toutes_les_listes[i][j] = age_counts.get(tranche, 0)

    # ============================================
    # 7. Répartition des problèmes par type de téléphone
    # ============================================
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']

    count_probleme_1 = [0] * len(ordered_type_tel)
    count_probleme_2 = [0] * len(ordered_type_tel)
    count_probleme_3 = [0] * len(ordered_type_tel)
    count_probleme_4 = [0] * len(ordered_type_tel)
    count_probleme_5 = [0] * len(ordered_type_tel)

    queryset = FactTable.objects.filter(id_question=9, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values('id_client__type_tel', 'id_reponse__problemes').annotate(total=Count('id'))

    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__problemes']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_probleme_1[idx] += count
        elif probleme_type == '2':
            count_probleme_2[idx] += count
        elif probleme_type == '3':
            count_probleme_3[idx] += count
        elif probleme_type == '4':
            count_probleme_4[idx] += count
        elif probleme_type == '5':
            count_probleme_5[idx] += count

    # ============================================
    # 8. Envoi des données au template
    # ============================================
    context = {
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'totalProblemOffre': totalProblemOffre,
        'totalProblems': totalProblems,
        'InternetLimite': round(InternetLimite, 2),
        'DataViteEpuisee': round(DataViteEpuisee, 2),
        'ValiditeCourte': round(ValiditeCourte, 2),
        'OffreFloue': round(OffreFloue, 2),
        'ChangementNonPossible': round(ChangementNonPossible, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'nombre_probleme_5': nombre_p5,
        'bu_list': bu_list,
        'probleme1_counts': probleme1_counts,
        'probleme2_counts': probleme2_counts,
        'probleme3_counts': probleme3_counts,
        'probleme4_counts': probleme4_counts,
        'probleme5_counts': probleme5_counts,
        'age_ranges': age_ranges,
        'data_probleme_1': data_probleme_1,
        'data_probleme_2': data_probleme_2,
        'data_probleme_3': data_probleme_3,
        'data_probleme_4': data_probleme_4,
        'data_probleme_5': data_probleme_5,
        'count_probleme_1': count_probleme_1,
        'count_probleme_2': count_probleme_2,
        'count_probleme_3': count_probleme_3,
        'count_probleme_4': count_probleme_4,
        'count_probleme_5': count_probleme_5,
    }

    return render(request, 'offre.html', context)


def problem_tarification(request):
    # ========================================
    # === RÉCUPÉRATION DES FILTRES DE REQUÊTE ==
    # ========================================
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # ============================================
    # === CALCUL DU TOTAL DE PROBLÈMES CLIENTS ===
    # ============================================
    totalProblems1 = FactTable.objects.filter(
        id_question__in=[6, 9, 14],
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblems1 = totalProblems1.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems1 = totalProblems1.filter(id_date__mois__gte=7)
    totalProblems1 = totalProblems1.count()

    totalProblems2 = FactTable.objects.filter(
        id_question=4,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes_appel__isnull=True
    ).exclude(
        id_reponse__problemes_appel=""
    ).exclude(
        id_reponse__problemes_appel="VIDE"
    ).exclude(
        id_reponse__problemes_appel="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblems2 = totalProblems2.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems2 = totalProblems2.filter(id_date__mois__gte=7)
    totalProblems2 = totalProblems2.count()

    totalProblems = totalProblems1 + totalProblems2

    # =================================================
    # === CALCUL DES POURCENTAGES POUR LA TARIFICATION ===
    # =================================================
    totalProblemsTarification = FactTable.objects.filter(
        id_question=12,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblemsTarification = totalProblemsTarification.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblemsTarification = totalProblemsTarification.filter(id_date__mois__gte=7)
    totalProblemsTarification = totalProblemsTarification.count()

    filtered_question = FactTable.objects.filter(
        id_question=12,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question_count = filtered_question.count()

    response_count = filtered_question.values(
        'id_reponse__problemes'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__problemes']: item['count']
        for item in response_count
    }

    OffresCouteuses = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    InternetCher = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PrixTelephoneEleve = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PrixModemEleve = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # =========================================
    # === DIAGRAMME ÉVOLUTION MENSUELLE ======
    # =========================================
    PROBLEMES_CODES = ["1", "2", "3", "4"]
    base_query = FactTable.objects.filter(
        id_question=12,
        id_reponse__problemes__in=PROBLEMES_CODES,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__problemes="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__problemes="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__problemes="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__problemes="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

    mois_set = set()
    for qs in [qs_p1, qs_p2, qs_p3, qs_p4]:
        for item in qs:
            mois_set.add(f"{item['label']:02d}")
    liste_mois = sorted(mois_set)

    def qs_to_dict(qs):
        return {f"{item['label']:02d}": item['nb_clients'] for item in qs}

    dict_p1 = qs_to_dict(qs_p1)
    dict_p2 = qs_to_dict(qs_p2)
    dict_p3 = qs_to_dict(qs_p3)
    dict_p4 = qs_to_dict(qs_p4)

    def build_count_list(d):
        return [d.get(mois, 0) for mois in liste_mois]

    nombre_p1 = build_count_list(dict_p1)
    nombre_p2 = build_count_list(dict_p2)
    nombre_p3 = build_count_list(dict_p3)
    nombre_p4 = build_count_list(dict_p4)

    # ============================
    # === RÉPARTITION PAR BU ====
    # ============================
    base_queryset = FactTable.objects.filter(id_question=12, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)

    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts = []
    probleme2_counts = []
    probleme3_counts = []
    probleme4_counts = []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        probleme1_counts.append(bu_queryset.filter(id_reponse__problemes="1").count())
        probleme2_counts.append(bu_queryset.filter(id_reponse__problemes="2").count())
        probleme3_counts.append(bu_queryset.filter(id_reponse__problemes="3").count())
        probleme4_counts.append(bu_queryset.filter(id_reponse__problemes="4").count())
        bu_list.append(bu)

    # ==========================================
    # === RÉPARTITION PAR TRANCHE D’ÂGE =======
    # ==========================================
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    probleme_ids = ["1", "2", "3", "4", "5"]
    data_probleme_1 = [0] * len(age_ranges)
    data_probleme_2 = [0] * len(age_ranges)
    data_probleme_3 = [0] * len(age_ranges)
    data_probleme_4 = [0] * len(age_ranges)
    data_probleme_5 = [0] * len(age_ranges)
    toutes_les_listes = [data_probleme_1, data_probleme_2, data_probleme_3, data_probleme_4, data_probleme_5]

    for i, probleme_id in enumerate(probleme_ids):
        reponses = FactTable.objects.filter(
            id_question=12,
            id_reponse__problemes=probleme_id,
            id_date__annee=annee_int
        )
        if filtre1 == '1':
            reponses = reponses.filter(id_date__mois__lte=6)
        elif filtre1 == '2':
            reponses = reponses.filter(id_date__mois__gte=7)
        comptage = reponses.values('id_client__age_abonne').annotate(count=Count('id'))
        age_counts = {r['id_client__age_abonne'] or 'Unknown': r['count'] for r in comptage}
        for j, tranche in enumerate(age_ranges):
            toutes_les_listes[i][j] = age_counts.get(tranche, 0)

    # ============================================
    # === RÉPARTITION PAR TYPE DE TÉLÉPHONE ======
    # ============================================
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']
    count_probleme_1 = [0] * len(ordered_type_tel)
    count_probleme_2 = [0] * len(ordered_type_tel)
    count_probleme_3 = [0] * len(ordered_type_tel)
    count_probleme_4 = [0] * len(ordered_type_tel)

    queryset = FactTable.objects.filter(id_question=12, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values('id_client__type_tel', 'id_reponse__problemes').annotate(total=Count('id'))

    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__problemes']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_probleme_1[idx] += count
        elif probleme_type == '2':
            count_probleme_2[idx] += count
        elif probleme_type == '3':
            count_probleme_3[idx] += count
        elif probleme_type == '4':
            count_probleme_4[idx] += count

    # =========================================
    # === RÉPARTITION PAR TYPE D’OFFRE ========
    # =========================================
    target_offers = [
        'Newhaylabezzef', 'DJEZZY_HAYLABEZZEF', 'Lowvalue',
        'Mixteprepaid', 'DJEZZY_HAYLAMAXI', 'DjezzyCarte_NEW',
        'Offrejeune', 'Hadraprepaid', 'Individual Hybrid'
    ]
    offer_labels = target_offers + ['Other']
    count_probleme_1_offre = [0] * len(offer_labels)
    count_probleme_2_offre = [0] * len(offer_labels)
    count_probleme_3_offre = [0] * len(offer_labels)
    count_probleme_4_offre = [0] * len(offer_labels)

    queryset_offre = FactTable.objects.filter(id_question=12, id_date__annee=annee_int).annotate(
        offre_group=Case(
            *[When(id_client__globale_profile=offer, then=Value(offer)) for offer in target_offers],
            default=Value('Other'),
            output_field=CharField()
        )
    )
    if filtre1 == '1':
        queryset_offre = queryset_offre.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset_offre = queryset_offre.filter(id_date__mois__gte=7)
    aggregation_offre = queryset_offre.values('offre_group', 'id_reponse__problemes').annotate(total=Count('id')).order_by()

    for item in aggregation_offre:
        offre_group = item['offre_group'] or 'Other'
        probleme_type = item['id_reponse__problemes']
        count = item['total']
        idx = offer_labels.index(offre_group)
        if probleme_type == '1':
            count_probleme_1_offre[idx] += count
        elif probleme_type == '2':
            count_probleme_2_offre[idx] += count
        elif probleme_type == '3':
            count_probleme_3_offre[idx] += count
        elif probleme_type == '4':
            count_probleme_4_offre[idx] += count

    # =======================================
    # === CONTEXTE À RETOURNER AU TEMPLATE ==
    # =======================================
    context = {
        'totalProblemsTarification': totalProblemsTarification,
        'totalProblems': totalProblems,
        'OffresCouteuses': round(OffresCouteuses, 2),
        'InternetCher': round(InternetCher, 2),
        'PrixTelephoneEleve': round(PrixTelephoneEleve, 2),
        'PrixModemEleve': round(PrixModemEleve, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'probleme1_counts': probleme1_counts,
        'probleme2_counts': probleme2_counts,
        'probleme3_counts': probleme3_counts,
        'probleme4_counts': probleme4_counts,
        'age_ranges': age_ranges,
        'data_probleme_1': data_probleme_1,
        'data_probleme_2': data_probleme_2,
        'data_probleme_3': data_probleme_3,
        'data_probleme_4': data_probleme_4,
        'count_probleme_1': count_probleme_1,
        'count_probleme_2': count_probleme_2,
        'count_probleme_3': count_probleme_3,
        'count_probleme_4': count_probleme_4,
        'offer_labels': offer_labels,
        'count_probleme_1_offre': count_probleme_1_offre,
        'count_probleme_2_offre': count_probleme_2_offre,
        'count_probleme_3_offre': count_probleme_3_offre,
        'count_probleme_4_offre': count_probleme_4_offre,
    }

    return render(request, 'tarification.html', context)



def problem_service(request):
    # ======================= 1. Récupération des paramètres =======================
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # ======================= 2. Total des problèmes =======================
    # Problèmes Internet, Offre, Tarification
    totalProblems1 = FactTable.objects.filter(
        id_question__in=[6, 9, 12],
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblems1 = totalProblems1.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems1 = totalProblems1.filter(id_date__mois__gte=7)
    totalProblems1 = totalProblems1.count()

    # Problèmes Appels
    totalProblems2 = FactTable.objects.filter(
        id_question=4,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes_appel__isnull=True
    ).exclude(
        id_reponse__problemes_appel=""
    ).exclude(
        id_reponse__problemes_appel="VIDE"
    ).exclude(
        id_reponse__problemes_appel="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblems2 = totalProblems2.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblems2 = totalProblems2.filter(id_date__mois__gte=7)
    totalProblems2 = totalProblems2.count()

    totalProblems = totalProblems1 + totalProblems2

    # Problèmes liés au service
    totalProblemsservice = FactTable.objects.filter(
        id_question=14,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        totalProblemsservice = totalProblemsservice.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        totalProblemsservice = totalProblemsservice.filter(id_date__mois__gte=7)
    totalProblemsservice = totalProblemsservice.count()

    # ======================= 3. Statistiques par type de problème (pourcentage) =======================
    filtered_question = FactTable.objects.filter(
        id_question=14,
        id_date__annee=annee_int
    ).exclude(
        id_reponse__problemes__isnull=True
    ).exclude(
        id_reponse__problemes=""
    ).exclude(
        id_reponse__problemes="VIDE"
    ).exclude(
        id_reponse__problemes="UNKNOWN"
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question_count = filtered_question.count()

    response_count = filtered_question.values('id_reponse__problemes').annotate(count=Count('id'))
    response_dict = {
        item['id_reponse__problemes']: item['count']
        for item in response_count
    }

    AttenteProlongee = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    RéclamationsIgnorees = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PersonnelMalpoli = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    AgenceTropLoin = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    OffreIndisponible = (response_dict.get("5", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # ======================= 4. Évolution mensuelle par type de problème =======================
    PROBLEMES_CODES = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=14,
        id_reponse__problemes__in=PROBLEMES_CODES,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__problemes="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__problemes="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__problemes="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__problemes="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__problemes="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

    mois_set = set()
    for qs in [qs_p1, qs_p2, qs_p3, qs_p4, qs_p5]:
        for item in qs:
            mois_set.add(f"{item['label']:02d}")
    liste_mois = sorted(mois_set)

    def qs_to_dict(qs):
        return {f"{item['label']:02d}": item['nb_clients'] for item in qs}

    dict_p1 = qs_to_dict(qs_p1)
    dict_p2 = qs_to_dict(qs_p2)
    dict_p3 = qs_to_dict(qs_p3)
    dict_p4 = qs_to_dict(qs_p4)
    dict_p5 = qs_to_dict(qs_p5)

    def build_count_list(d):
        return [d.get(mois, 0) for mois in liste_mois]

    nombre_p1 = build_count_list(dict_p1)
    nombre_p2 = build_count_list(dict_p2)
    nombre_p3 = build_count_list(dict_p3)
    nombre_p4 = build_count_list(dict_p4)
    nombre_p5 = build_count_list(dict_p5)

    # ======================= 5. Répartition des problèmes par BU =======================
    base_queryset = FactTable.objects.filter(id_question=14, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)

    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts, probleme2_counts, probleme3_counts, probleme4_counts, probleme5_counts = [], [], [], [], []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        probleme1_counts.append(bu_queryset.filter(id_reponse__problemes="1").count())
        probleme2_counts.append(bu_queryset.filter(id_reponse__problemes="2").count())
        probleme3_counts.append(bu_queryset.filter(id_reponse__problemes="3").count())
        probleme4_counts.append(bu_queryset.filter(id_reponse__problemes="4").count())
        probleme5_counts.append(bu_queryset.filter(id_reponse__problemes="5").count())
        bu_list.append(bu)

    # ======================= 6. Répartition par tranche d’âge =======================
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    probleme_ids = ["1", "2", "3", "4", "5"]

    data_probleme_1 = [0] * len(age_ranges)
    data_probleme_2 = [0] * len(age_ranges)
    data_probleme_3 = [0] * len(age_ranges)
    data_probleme_4 = [0] * len(age_ranges)
    data_probleme_5 = [0] * len(age_ranges)

    toutes_les_listes = [data_probleme_1, data_probleme_2, data_probleme_3, data_probleme_4, data_probleme_5]

    for i, probleme_id in enumerate(probleme_ids):
        reponses = FactTable.objects.filter(
            id_question=14,
            id_reponse__problemes=probleme_id,
            id_date__annee=annee_int
        )
        if filtre1 == '1':
            reponses = reponses.filter(id_date__mois__lte=6)
        elif filtre1 == '2':
            reponses = reponses.filter(id_date__mois__gte=7)
        comptage = reponses.values('id_client__age_abonne').annotate(count=Count('id'))
        age_counts = {r['id_client__age_abonne'] or 'Unknown': r['count'] for r in comptage}
        for j, tranche in enumerate(age_ranges):
            toutes_les_listes[i][j] = age_counts.get(tranche, 0)

    # ======================= 7. Répartition par type de téléphone =======================
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']

    count_probleme_1 = [0] * len(ordered_type_tel)
    count_probleme_2 = [0] * len(ordered_type_tel)
    count_probleme_3 = [0] * len(ordered_type_tel)
    count_probleme_4 = [0] * len(ordered_type_tel)
    count_probleme_5 = [0] * len(ordered_type_tel)

    queryset = FactTable.objects.filter(id_question=14, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values('id_client__type_tel', 'id_reponse__problemes').annotate(total=Count('id'))

    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__problemes']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_probleme_1[idx] += count
        elif probleme_type == '2':
            count_probleme_2[idx] += count
        elif probleme_type == '3':
            count_probleme_3[idx] += count
        elif probleme_type == '4':
            count_probleme_4[idx] += count
        elif probleme_type == '5':
            count_probleme_5[idx] += count

    # ======================= 8. Contexte et rendu =======================
    context = {
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'totalProblemsservice': totalProblemsservice,
        'totalProblems': totalProblems,
        'AttenteProlongee': round(AttenteProlongee, 2),
        'RéclamationsIgnorees': round(RéclamationsIgnorees, 2),
        'PersonnelMalpoli': round(PersonnelMalpoli, 2),
        'AgenceTropLoin': round(AgenceTropLoin, 2),
        'OffreIndisponible': round(OffreIndisponible, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'nombre_probleme_5': nombre_p5,
        'bu_list': bu_list,
        'probleme1_counts': probleme1_counts,
        'probleme2_counts': probleme2_counts,
        'probleme3_counts': probleme3_counts,
        'probleme4_counts': probleme4_counts,
        'probleme5_counts': probleme5_counts,
        'age_ranges': age_ranges,
        'data_probleme_1': data_probleme_1,
        'data_probleme_2': data_probleme_2,
        'data_probleme_3': data_probleme_3,
        'data_probleme_4': data_probleme_4,
        'data_probleme_5': data_probleme_5,
        'count_probleme_1': count_probleme_1,
        'count_probleme_2': count_probleme_2,
        'count_probleme_3': count_probleme_3,
        'count_probleme_4': count_probleme_4,
        'count_probleme_5': count_probleme_5,
    }

    return render(request, 'service.html', context)


def problem_general(request):
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # Compter les problèmes pour id_question = 5 (tous taux confondus)
    base_total = FactTable.objects.filter(
        id_question=5,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_total = base_total.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_total = base_total.filter(id_date__mois__gte=7)
    total_count = base_total.count()

    # Comptage par taux (1 à 5) avec le même filtre
    taux_counts = base_total.values('id_reponse__satis_insatis').annotate(total=Count('id'))
    taux_dict = {row['id_reponse__satis_insatis']: row['total'] for row in taux_counts}

    taux_1 = (taux_dict.get("1", 0) )  if total_count else 0
    taux_2 = (taux_dict.get("2", 0))   if total_count else 0
    taux_3 = (taux_dict.get("3", 0) )  if total_count else 0
    taux_4 = (taux_dict.get("4", 0) )  if total_count else 0
    taux_5 = (taux_dict.get("5", 0) )  if total_count else 0

    # Évolution mensuelle par type de problème (déjà filtré plus bas)
    PROBLEMES_CODES = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=5,
        id_reponse__satis_insatis__in=PROBLEMES_CODES,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__satis_insatis="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__satis_insatis="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__satis_insatis="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__satis_insatis="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__satis_insatis="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

    mois_set = set()
    for qs in [qs_p1, qs_p2, qs_p3, qs_p4, qs_p5]:
        for item in qs:
            mois_set.add(f"{item['label']:02d}")
    liste_mois = sorted(mois_set)

    def qs_to_dict(qs):
        return {f"{item['label']:02d}": item['nb_clients'] for item in qs}

    dict_p1 = qs_to_dict(qs_p1)
    dict_p2 = qs_to_dict(qs_p2)
    dict_p3 = qs_to_dict(qs_p3)
    dict_p4 = qs_to_dict(qs_p4)
    dict_p5 = qs_to_dict(qs_p5)

    def build_count_list(d):
        return [d.get(mois, 0) for mois in liste_mois]

    nombre_p1 = build_count_list(dict_p1)
    nombre_p2 = build_count_list(dict_p2)
    nombre_p3 = build_count_list(dict_p3)
    nombre_p4 = build_count_list(dict_p4)
    nombre_p5 = build_count_list(dict_p5)

    # Répartition par BU (avec filtre année et semestre)
    base_queryset = FactTable.objects.filter(id_question=5, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)

    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts, probleme2_counts, probleme3_counts, probleme4_counts, probleme5_counts = [], [], [], [], []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        probleme1_counts.append(bu_queryset.filter(id_reponse__satis_insatis="1").count())
        probleme2_counts.append(bu_queryset.filter(id_reponse__satis_insatis="2").count())
        probleme3_counts.append(bu_queryset.filter(id_reponse__satis_insatis="3").count())
        probleme4_counts.append(bu_queryset.filter(id_reponse__satis_insatis="4").count())
        probleme5_counts.append(bu_queryset.filter(id_reponse__satis_insatis="5").count())
        bu_list.append(bu)

    context = {
        'p1': round(taux_1, 2),
        'p2': round(taux_2, 2),
        'p3': round(taux_3, 2),
        'p4': round(taux_4, 2),
        'p5': round(taux_5, 2),
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'nombre_probleme_5': nombre_p5,
        'liste_mois': liste_mois,
        'bu_list': bu_list,
        'probleme1_counts': probleme1_counts,
        'probleme2_counts': probleme2_counts,
        'probleme3_counts': probleme3_counts,
        'probleme4_counts': probleme4_counts,
        'probleme5_counts': probleme5_counts,
    }

    return render(request, 'problem_home.html', context)

