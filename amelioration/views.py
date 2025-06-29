from django.shortcuts import render
from satisfaction_client.models import FactTable ,DimTemps
from django.db.models import Count, F
from django.db.models import Count, Case, When, Value, CharField



def amelioration_tarification(request):
    # --- Récupération des filtres depuis l'URL ---
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[0] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # --- Total des réponses pertinentes (toutes questions sauf tarification) ---
    total_query = FactTable.objects.filter(
        id_question__in=[15, 11, 16, 10]
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        total_query = total_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        total_query = total_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        total_query = total_query.filter(id_date__mois__gte=7)
    Total = total_query.count()

    # --- Total des réponses à la question 8 (tarification) avec amélioration renseignée ---
    base_total_tarif = FactTable.objects.filter(
        id_question=8,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_total_tarif = base_total_tarif.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_total_tarif = base_total_tarif.filter(id_date__mois__gte=7)
    TotalTarification = base_total_tarif.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    ).count()

    # --- Analyse des proportions d'amélioration pour la question 8 ---
    filtered_question = FactTable.objects.filter(
        id_question=8,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question = filtered_question.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    filtered_question_count = filtered_question.count()

    # Compter les réponses par type d'amélioration
    response_count = filtered_question.values(
        'id_reponse__amelioraion_plus'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__amelioraion_plus']: item['count']
        for item in response_count
    }

    # Calcul des pourcentages par type d'amélioration
    PrixOffres = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PrixInternet = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PrixTéléphones = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PrixModems = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # --- Données mensuelles par type d’amélioration ---
    AMELIORATION_CODE = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=8,
        id_reponse__amelioraion_plus__in=AMELIORATION_CODE,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__amelioraion_plus="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__amelioraion_plus="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__amelioraion_plus="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__amelioraion_plus="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

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

    # --- Répartition par BU ---
    base_queryset = FactTable.objects.filter(id_question=8, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)

    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    amelioration1_counts = []
    amelioration2_counts = []
    amelioration3_counts = []
    amelioration4_counts = []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        amelioration1_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="1").count())
        amelioration2_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="2").count())
        amelioration3_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="3").count())
        amelioration4_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="4").count())
        bu_list.append(bu)

    # --- Répartition par tranche d’âge ---
    # --- Répartition par tranche d’âge ---
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    amelioration_ids = ["1", "2", "3", "4"]
    data_amelio_1 = [0] * len(age_ranges)
    data_amelio_2 = [0] * len(age_ranges)
    data_amelio_3 = [0] * len(age_ranges)
    data_amelio_4 = [0] * len(age_ranges)
    toutes_les_listes = [data_amelio_1, data_amelio_2, data_amelio_3, data_amelio_4]

    for i, amelio_id in enumerate(amelioration_ids):
        reponses = FactTable.objects.filter(
            id_question=8,
            id_reponse__amelioraion_plus=amelio_id,
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

    # --- Répartition par type de téléphone ---
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']
    count_amelio_1 = [0] * len(ordered_type_tel)
    count_amelio_2 = [0] * len(ordered_type_tel)
    count_amelio_3 = [0] * len(ordered_type_tel)
    count_amelio_4 = [0] * len(ordered_type_tel)

    queryset = FactTable.objects.filter(id_question=8, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values(
        'id_client__type_tel',
        'id_reponse__amelioraion_plus'
    ).annotate(
        total=Count('id')
    ).order_by()

    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__amelioraion_plus']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_amelio_1[idx] += count
        elif probleme_type == '2':
            count_amelio_2[idx] += count
        elif probleme_type == '3':
            count_amelio_3[idx] += count
        elif probleme_type == '4':
            count_amelio_4[idx] += count

    # --- Construction du contexte pour le template ---
    context = {
        'TotalTarification': TotalTarification,
        'Total': Total,
        'PrixOffres': round(PrixOffres, 2),
        'PrixInternet': round(PrixInternet, 2),
        'PrixTéléphones': round(PrixTéléphones, 2),
        'PrixModems': round(PrixModems, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'amelioration1_counts': amelioration1_counts,
        'amelioration2_counts': amelioration2_counts,
        'amelioration3_counts': amelioration3_counts,
        'amelioration4_counts': amelioration4_counts,
        'age_ranges': age_ranges,
        'data_amelio_1': data_amelio_1,
        'data_amelio_2': data_amelio_2,
        'data_amelio_3': data_amelio_3,
        'data_amelio_4': data_amelio_4,
        'count_amelio_1': count_amelio_1,
        'count_amelio_2': count_amelio_2,
        'count_amelio_3': count_amelio_3,
        'count_amelio_4': count_amelio_4,
    }

    return render(request, 'amelioration_tarification.html', context)






# --- Appel ---
def amelioration_appel(request):
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[0] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # --- Total des réponses pertinentes (toutes questions sauf appel) ---
    total_query = FactTable.objects.filter(
        id_question__in=[15, 11, 8, 10]
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        total_query = total_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        total_query = total_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        total_query = total_query.filter(id_date__mois__gte=7)
    Total = total_query.count()

    # --- Total des réponses à la question 16 (appel) avec amélioration renseignée ---
    base_total_appel = FactTable.objects.filter(
        id_question=16,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_total_appel = base_total_appel.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_total_appel = base_total_appel.filter(id_date__mois__gte=7)
    TotalAppel = base_total_appel.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    ).count()

    # --- Analyse des proportions d'amélioration pour la question 16 ---
    filtered_question = FactTable.objects.filter(
        id_question=16,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question = filtered_question.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    filtered_question_count = filtered_question.count()
    response_count = filtered_question.values(
        'id_reponse__amelioraion_plus'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__amelioraion_plus']: item['count']
        for item in response_count
    }
    ReseauFaible = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    AppelInterrompus = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    QualiteFaible = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PAppelEchoue = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # --- Données mensuelles par type d’amélioration ---
    AMELIORATION_CODE = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=16,
        id_reponse__amelioraion_plus__in=AMELIORATION_CODE,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)
    qs_p1 = base_query.filter(id_reponse__amelioraion_plus="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__amelioraion_plus="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__amelioraion_plus="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__amelioraion_plus="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__amelioraion_plus="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
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

    # --- Répartition par BU ---
    base_queryset = FactTable.objects.filter(id_question=16, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)
    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()
    bu_list = []
    amelioration1_counts = []
    amelioration2_counts = []
    amelioration3_counts = []
    amelioration4_counts = []
    amelioration5_counts = []
    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        amelioration1_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="1").count())
        amelioration2_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="2").count())
        amelioration3_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="3").count())
        amelioration4_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="4").count())
        amelioration5_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="5").count())
        bu_list.append(bu)

    # --- Répartition par tranche d’âge ---
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    amelioration_ids = ["1", "2", "3", "4", "5"]
    data_amelio_1 = [0] * len(age_ranges)
    data_amelio_2 = [0] * len(age_ranges)
    data_amelio_3 = [0] * len(age_ranges)
    data_amelio_4 = [0] * len(age_ranges)
    data_amelio_5 = [0] * len(age_ranges)
    toutes_les_listes = [data_amelio_1, data_amelio_2, data_amelio_3, data_amelio_4, data_amelio_5]
    for i, amelio_id in enumerate(amelioration_ids):
        reponses = FactTable.objects.filter(
            id_question=16,
            id_reponse__amelioraion_plus=amelio_id,
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

    # --- Répartition par type de téléphone ---
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']
    count_amelio_1 = [0] * len(ordered_type_tel)
    count_amelio_2 = [0] * len(ordered_type_tel)
    count_amelio_3 = [0] * len(ordered_type_tel)
    count_amelio_4 = [0] * len(ordered_type_tel)
    queryset = FactTable.objects.filter(id_question=16, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values(
        'id_client__type_tel',
        'id_reponse__amelioraion_plus'
    ).annotate(
        total=Count('id')
    ).order_by()
    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__amelioraion_plus']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_amelio_1[idx] += count
        elif probleme_type == '2':
            count_amelio_2[idx] += count
        elif probleme_type == '3':
            count_amelio_3[idx] += count
        elif probleme_type == '4':
            count_amelio_4[idx] += count

    context = {
        'TotalAppel': TotalAppel,
        'Total': Total,
        'ReseauFaible': round(ReseauFaible, 2),
        'AppelInterrompus': round(AppelInterrompus, 2),
        'QualiteFaible': round(QualiteFaible, 2),
        'PAppelEchoue': round(PAppelEchoue, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'nombre_probleme_5': nombre_p5,
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'amelioration1_counts': amelioration1_counts,
        'amelioration2_counts': amelioration2_counts,
        'amelioration3_counts': amelioration3_counts,
        'amelioration4_counts': amelioration4_counts,
        'amelioration5_counts': amelioration5_counts,
        'age_ranges': age_ranges,
        'data_amelio_1': data_amelio_1,
        'data_amelio_2': data_amelio_2,
        'data_amelio_3': data_amelio_3,
        'data_amelio_4': data_amelio_4,
        'data_amelio_5': data_amelio_5,
        'count_amelio_1': count_amelio_1,
        'count_amelio_2': count_amelio_2,
        'count_amelio_3': count_amelio_3,
        'count_amelio_4': count_amelio_4,
    }
    return render(request, 'amelioration_appel.html', context)







def amelioration_internet(request):
    # Récupération des années distinctes disponibles dans la table DimTemps
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[0] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # Total des réponses aux questions d'amélioration (filtrées par valeur valide)
    total_query = FactTable.objects.filter(
        id_question__in=[15, 16, 8, 10]
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        total_query = total_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        total_query = total_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        total_query = total_query.filter(id_date__mois__gte=7)
    Total = total_query.count()

    # Total des réponses à la question d’intérêt pour Internet
    base_total_interet = FactTable.objects.filter(
        id_question=11,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_total_interet = base_total_interet.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_total_interet = base_total_interet.filter(id_date__mois__gte=7)
    TotalInteret = base_total_interet.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    ).count()

    # Statistiques globales (en %)
    filtered_question = FactTable.objects.filter(
        id_question=11,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question = filtered_question.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    filtered_question_count = filtered_question.count()
    response_count = filtered_question.values(
        'id_reponse__amelioraion_plus'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__amelioraion_plus']: item['count']
        for item in response_count
    }
    VitesseInternet = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    CoupureInternet = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    NonReseau = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    FaibleReseau = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # Évolution mensuelle
    AMELIORATION_CODE = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=11,
        id_reponse__amelioraion_plus__in=AMELIORATION_CODE,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)
    qs_p1 = base_query.filter(id_reponse__amelioraion_plus="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__amelioraion_plus="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__amelioraion_plus="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__amelioraion_plus="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__amelioraion_plus="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
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

    # Répartition par BU
    base_queryset = FactTable.objects.filter(id_question=11, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)
    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()
    bu_list = []
    amelioration1_counts = []
    amelioration2_counts = []
    amelioration3_counts = []
    amelioration4_counts = []
    amelioration5_counts = []
    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        amelioration1_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="1").count())
        amelioration2_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="2").count())
        amelioration3_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="3").count())
        amelioration4_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="4").count())
        amelioration5_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="5").count())
        bu_list.append(bu)

    # Répartition par tranche d’âge
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    amelioration_ids = ["1", "2", "3", "4", "5"]
    data_amelio_1 = [0] * len(age_ranges)
    data_amelio_2 = [0] * len(age_ranges)
    data_amelio_3 = [0] * len(age_ranges)
    data_amelio_4 = [0] * len(age_ranges)
    data_amelio_5 = [0] * len(age_ranges)
    toutes_les_listes = [data_amelio_1, data_amelio_2, data_amelio_3, data_amelio_4, data_amelio_5]
    for i, amelio_id in enumerate(amelioration_ids):
        reponses = FactTable.objects.filter(
            id_question=11,
            id_reponse__amelioraion_plus=amelio_id,
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

    # Répartition par type de téléphone
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']
    count_amelio_1 = [0] * len(ordered_type_tel)
    count_amelio_2 = [0] * len(ordered_type_tel)
    count_amelio_3 = [0] * len(ordered_type_tel)
    count_amelio_4 = [0] * len(ordered_type_tel)
    queryset = FactTable.objects.filter(id_question=11, id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values(
        'id_client__type_tel',
        'id_reponse__amelioraion_plus'
    ).annotate(
        total=Count('id')
    ).order_by()
    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__amelioraion_plus']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_amelio_1[idx] += count
        elif probleme_type == '2':
            count_amelio_2[idx] += count
        elif probleme_type == '3':
            count_amelio_3[idx] += count
        elif probleme_type == '4':
            count_amelio_4[idx] += count

    context = {
        'TotalInteret': TotalInteret,
        'Total': Total,
        'VitesseInternet': round(VitesseInternet, 2),
        'CoupureInternet': round(CoupureInternet, 2),
        'NonReseau': round(NonReseau, 2),
        'FaibleReseau': round(FaibleReseau, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'nombre_probleme_5': nombre_p5,
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'amelioration1_counts': amelioration1_counts,
        'amelioration2_counts': amelioration2_counts,
        'amelioration3_counts': amelioration3_counts,
        'amelioration4_counts': amelioration4_counts,
        'amelioration5_counts': amelioration5_counts,
        'age_ranges': age_ranges,
        'data_amelio_1': data_amelio_1,
        'data_amelio_2': data_amelio_2,
        'data_amelio_3': data_amelio_3,
        'data_amelio_4': data_amelio_4,
        'data_amelio_5': data_amelio_5,
        'count_amelio_1': count_amelio_1,
        'count_amelio_2': count_amelio_2,
        'count_amelio_3': count_amelio_3,
        'count_amelio_4': count_amelio_4,
    }
    return render(request, 'amelioration_internet.html', context)


def amelioration_service(request):
    # Récupérer la liste des années distinctes ordonnée décroissante
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[0] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # Comptage total des réponses aux questions 11,16,8,10 avec amelioraion_plus valide
    total_query = FactTable.objects.filter(
        id_question__in=[11, 16, 8, 10]
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        total_query = total_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        total_query = total_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        total_query = total_query.filter(id_date__mois__gte=7)
    Total = total_query.count()

    # Comptage total des réponses à la question 15 avec amelioraion_plus valide
    base_total_service = FactTable.objects.filter(
        id_question=15,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_total_service = base_total_service.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_total_service = base_total_service.filter(id_date__mois__gte=7)
    TotalService = base_total_service.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    ).count()

    # Filtrage des réponses à la question 15 avec amelioraion_plus valide
    filtered_question = FactTable.objects.filter(
        id_question=15,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question = filtered_question.exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    filtered_question_count = filtered_question.count()

    # Comptage par type d'amélioration
    response_count = filtered_question.values(
        'id_reponse__amelioraion_plus'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__amelioraion_plus']: item['count']
        for item in response_count
    }
    AttenteProlongee = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    RéclamationsIgnorees = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    PersonnelMalpoli = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    AgenceTropLoin = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    OffreIndisponible = (response_dict.get("5", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # Base de requête sur les codes d'amélioration valides
    AMELIORATION_CODE = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=15,
        id_reponse__amelioraion_plus__in=AMELIORATION_CODE,
        id_date__annee=annee_int
    )
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)
    qs_p1 = base_query.filter(id_reponse__amelioraion_plus="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__amelioraion_plus="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__amelioraion_plus="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__amelioraion_plus="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__amelioraion_plus="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
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

    # Analyse par BU (Business Unit) - question 15
    base_queryset = FactTable.objects.filter(id_question=15, id_date__annee=annee_int).exclude(id_region__bu="Other")
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)
    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()
    bu_list = []
    amelioration1_counts = []
    amelioration2_counts = []
    amelioration3_counts = []
    amelioration4_counts = []
    amelioration5_counts = []
    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        amelioration1_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="1").count())
        amelioration2_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="2").count())
        amelioration3_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="3").count())
        amelioration4_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="4").count())
        amelioration5_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="5").count())
        bu_list.append(bu)

    # Analyse par tranche d'âge pour chaque code amélioration
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    amelioration_ids = ["1", "2", "3", "4", "5"]
    data_amelio_1 = [0] * len(age_ranges)
    data_amelio_2 = [0] * len(age_ranges)
    data_amelio_3 = [0] * len(age_ranges)
    data_amelio_4 = [0] * len(age_ranges)
    data_amelio_5 = [0] * len(age_ranges)
    toutes_les_listes = [data_amelio_1, data_amelio_2, data_amelio_3, data_amelio_4, data_amelio_5]
    for i, amelio_id in enumerate(amelioration_ids):
        reponses = FactTable.objects.filter(
            id_question=15,
            id_reponse__amelioraion_plus=amelio_id,
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

     # Analyse par type de téléphone (question 14) avec filtres année et semestre appliqués
    type_tel_order = ['Phablet', 'Smartphone', 'Basic Phone', 'Feature Phone']
    ordered_type_tel = type_tel_order + ['Other']
    count_amelio_1 = [0] * len(ordered_type_tel)
    count_amelio_2 = [0] * len(ordered_type_tel)
    count_amelio_3 = [0] * len(ordered_type_tel)
    count_amelio_4 = [0] * len(ordered_type_tel)
    count_amelio_5 = [0] * len(ordered_type_tel)
    queryset = FactTable.objects.filter(id_question=14)
    if annee_int:
        queryset = queryset.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    aggregation = queryset.values(
        'id_client__type_tel',
        'id_reponse__problemes'
    ).annotate(
        total=Count('id')
    ).order_by()
    for item in aggregation:
        tel_type = item['id_client__type_tel'] or 'Other'
        probleme_type = item['id_reponse__problemes']
        count = item['total']
        idx = type_tel_order.index(tel_type) if tel_type in type_tel_order else len(type_tel_order)
        if probleme_type == '1':
            count_amelio_1[idx] += count
        elif probleme_type == '2':
            count_amelio_2[idx] += count
        elif probleme_type == '3':
            count_amelio_3[idx] += count
        elif probleme_type == '4':
            count_amelio_4[idx] += count
        elif probleme_type == '5':
            count_amelio_5[idx] += count

    context = {
        'TotalService': TotalService,
        'Total': Total,
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
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'amelioration1_counts': amelioration1_counts,
        'amelioration2_counts': amelioration2_counts,
        'amelioration3_counts': amelioration3_counts,
        'amelioration4_counts': amelioration4_counts,
        'amelioration5_counts': amelioration5_counts,
        'age_ranges': age_ranges,
        'data_amelio_1': data_amelio_1,
        'data_amelio_2': data_amelio_2,
        'data_amelio_3': data_amelio_3,
        'data_amelio_4': data_amelio_4,
        'data_amelio_5': data_amelio_5,
        'count_amelio_1': count_amelio_1,
        'count_amelio_2': count_amelio_2,
        'count_amelio_3': count_amelio_3,
        'count_amelio_4': count_amelio_4,
        'count_amelio_5': count_amelio_5,
    }
    return render(request, 'amelioration_service.html', context)



def amelioration_offre(request):
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[0] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # Total des réponses filtrées sur plusieurs questions (11, 16, 8, 15)
    total_query = FactTable.objects.filter(
        id_question__in=[11, 16, 8, 15]
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        total_query = total_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        total_query = total_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        total_query = total_query.filter(id_date__mois__gte=7)
    Total = total_query.count()

    # Total des réponses pour la question 10
    total_offre_query = FactTable.objects.filter(
        id_question=10
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        total_offre_query = total_offre_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        total_offre_query = total_offre_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        total_offre_query = total_offre_query.filter(id_date__mois__gte=7)
    TotalOffre = total_offre_query.count()

    # Filtrage des réponses pour la question 10
    filtered_question = FactTable.objects.filter(
        id_question=10
    ).exclude(
        id_reponse__amelioraion_plus__isnull=True
    ).exclude(
        id_reponse__amelioraion_plus=""
    ).exclude(
        id_reponse__amelioraion_plus="VIDE"
    ).exclude(
        id_reponse__amelioraion_plus="UNKNOWN"
    )
    if annee_int:
        filtered_question = filtered_question.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        filtered_question = filtered_question.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        filtered_question = filtered_question.filter(id_date__mois__gte=7)
    filtered_question_count = filtered_question.count()

    response_count = filtered_question.values(
        'id_reponse__amelioraion_plus'
    ).annotate(
        count=Count('id')
    )
    response_dict = {
        item['id_reponse__amelioraion_plus']: item['count']
        for item in response_count
    }
    VolumeInternetInsuffisant = (response_dict.get("1", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    DataViteEpuisée = (response_dict.get("2", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    ValiditéCourte = (response_dict.get("3", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    OffresFloues = (response_dict.get("4", 0) / filtered_question_count) * 100 if filtered_question_count else 0
    ChangementOffreImpossible = (response_dict.get("5", 0) / filtered_question_count) * 100 if filtered_question_count else 0

    # Codes d'amélioration utilisés pour filtrer
    AMELIORATION_CODE = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=10,
        id_reponse__amelioraion_plus__in=AMELIORATION_CODE
    )
    if annee_int:
        base_query = base_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)
    qs_p1 = base_query.filter(id_reponse__amelioraion_plus="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__amelioraion_plus="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__amelioraion_plus="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__amelioraion_plus="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__amelioraion_plus="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
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

    # Analyse par BU (Business Unit)
    base_queryset = FactTable.objects.filter(id_question=10)
    if annee_int:
        base_queryset = base_queryset.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)
    base_queryset = base_queryset.exclude(id_region__bu="Other")
    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()
    bu_list = []
    amelioration1_counts = []
    amelioration2_counts = []
    amelioration3_counts = []
    amelioration4_counts = []
    amelioration5_counts = []
    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        amelioration1_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="1").count())
        amelioration2_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="2").count())
        amelioration3_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="3").count())
        amelioration4_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="4").count())
        amelioration5_counts.append(bu_queryset.filter(id_reponse__amelioraion_plus="5").count())
        bu_list.append(bu)

    # Analyse par tranche d'âge
    age_ranges = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    amelioration_ids = ["1", "2", "3", "4", "5"]
    data_amelio_1 = [0] * len(age_ranges)
    data_amelio_2 = [0] * len(age_ranges)
    data_amelio_3 = [0] * len(age_ranges)
    data_amelio_4 = [0] * len(age_ranges)
    data_amelio_5 = [0] * len(age_ranges)
    toutes_les_listes = [data_amelio_1, data_amelio_2, data_amelio_3, data_amelio_4, data_amelio_5]
    for i, amelio_id in enumerate(amelioration_ids):
        reponses = FactTable.objects.filter(
            id_question=10,
            id_reponse__amelioraion_plus=amelio_id
        )
        if annee_int:
            reponses = reponses.filter(id_date__annee=annee_int)
        if filtre1 == '1':
            reponses = reponses.filter(id_date__mois__lte=6)
        elif filtre1 == '2':
            reponses = reponses.filter(id_date__mois__gte=7)
        comptage = reponses.values('id_client__age_abonne').annotate(count=Count('id'))
        age_counts = {r['id_client__age_abonne'] or 'Unknown': r['count'] for r in comptage}
        for j, tranche in enumerate(age_ranges):
            toutes_les_listes[i][j] = age_counts.get(tranche, 0)

    # Analyse par type d'offre cible
    target_offers = [
        'Newhaylabezzef', 'DJEZZY_HAYLABEZZEF', 'Lowvalue',
        'Mixteprepaid', 'DJEZZY_HAYLAMAXI', 'DjezzyCarte_NEW',
        'Offrejeune', 'Hadraprepaid', 'Individual Hybrid'
    ]
    offer_labels = target_offers + ['Other']
    count_amelio_1 = [0] * len(offer_labels)
    count_amelio_2 = [0] * len(offer_labels)
    count_amelio_3 = [0] * len(offer_labels)
    count_amelio_4 = [0] * len(offer_labels)
    count_amelio_5 = [0] * len(offer_labels)
    queryset = FactTable.objects.filter(id_question=10)
    if annee_int:
        queryset = queryset.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        queryset = queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        queryset = queryset.filter(id_date__mois__gte=7)
    queryset = queryset.annotate(
        offre_group=Case(
            *[When(id_client__globale_profile=offer, then=Value(offer)) for offer in target_offers],
            default=Value('Other'),
            output_field=CharField()
        )
    )
    aggregation = queryset.values(
        'offre_group',
        'id_reponse__amelioraion_plus'
    ).annotate(
        total=Count('id')
    ).order_by()
    for item in aggregation:
        offre_group = item['offre_group'] or 'Other'
        amelio_type = item['id_reponse__amelioraion_plus']
        count = item['total']
        idx = offer_labels.index(offre_group)
        if amelio_type == '1':
            count_amelio_1[idx] += count
        elif amelio_type == '2':
            count_amelio_2[idx] += count
        elif amelio_type == '3':
            count_amelio_3[idx] += count
        elif amelio_type == '4':
            count_amelio_4[idx] += count
        elif amelio_type == '5':
            count_amelio_5[idx] += count

    context = {
        'TotalOffre': TotalOffre,
        'Total': Total,
        'VolumeInternetInsuffisant': round(VolumeInternetInsuffisant, 2),
        'DataViteEpuisée': round(DataViteEpuisée, 2),
        'ValiditéCourte': round(ValiditéCourte, 2),
        'OffresFloues': round(OffresFloues, 2),
        'ChangementOffreImpossible': round(ChangementOffreImpossible, 2),
        'liste_mois': liste_mois,
        'nombre_probleme_1': nombre_p1,
        'nombre_probleme_2': nombre_p2,
        'nombre_probleme_3': nombre_p3,
        'nombre_probleme_4': nombre_p4,
        'nombre_probleme_5': nombre_p5,
        'annees': annees,
        'annee_selectionnee': annee_selectionnee,
        'mois_selectionne': filtre1,
        'bu_list': bu_list,
        'amelioration1_counts': amelioration1_counts,
        'amelioration2_counts': amelioration2_counts,
        'amelioration3_counts': amelioration3_counts,
        'amelioration4_counts': amelioration4_counts,
        'amelioration5_counts': amelioration5_counts,
        'age_ranges': age_ranges,
        'data_amelio_1': data_amelio_1,
        'data_amelio_2': data_amelio_2,
        'data_amelio_3': data_amelio_3,
        'data_amelio_4': data_amelio_4,
        'data_amelio_5': data_amelio_5,
        'count_amelio_1': count_amelio_1,
        'count_amelio_2': count_amelio_2,
        'count_amelio_3': count_amelio_3,
        'count_amelio_4': count_amelio_4,
        'count_amelio_5': count_amelio_5,
        'offer_labels': offer_labels,
    }
    return render(request, 'amelioration_offre.html', context)

def amelioration_home(request):
    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[0] if annees else None)
    annee_int = int(annee_selectionnee) if annee_selectionnee else None
    filtre1 = request.GET.get("mois")  # '1' pour S1, '2' pour S2, None pour toute l'année

    # Compter les problèmes pour id_question = 7 (avec filtres année/semestre)
    probleme_query = FactTable.objects.filter(
        id_question=7,
        id_reponse__amelioraion_passif__in=["1", "2", "3", "4", "5"]
    )
    if annee_int:
        probleme_query = probleme_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        probleme_query = probleme_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        probleme_query = probleme_query.filter(id_date__mois__gte=7)
    resultats = (
        probleme_query
        .values('id_reponse__amelioraion_passif')
        .annotate(total=Count('id'))
    )
    probleme_counts = {
        row['id_reponse__amelioraion_passif']: row['total']
        for row in resultats
    }

    PROBLEMES_CODES = ["1", "2", "3", "4", "5"]
    base_query = FactTable.objects.filter(
        id_question=7,
        id_reponse__amelioraion_passif__in=PROBLEMES_CODES
    )
    if annee_int:
        base_query = base_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        base_query = base_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(id_date__mois__gte=7)

    qs_p1 = base_query.filter(id_reponse__amelioraion_passif="1").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p2 = base_query.filter(id_reponse__amelioraion_passif="2").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p3 = base_query.filter(id_reponse__amelioraion_passif="3").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p4 = base_query.filter(id_reponse__amelioraion_passif="4").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')
    qs_p5 = base_query.filter(id_reponse__amelioraion_passif="5").values(label=F('id_date__mois')).annotate(nb_clients=Count('id')).order_by('label')

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

    # Analyse par BU (Business Unit) avec filtres année/semestre
    base_queryset = FactTable.objects.filter(id_question=7).exclude(id_region__bu="Other")
    if annee_int:
        base_queryset = base_queryset.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        base_queryset = base_queryset.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        base_queryset = base_queryset.filter(id_date__mois__gte=7)
    bus = base_queryset.values_list('id_region__bu', flat=True).distinct()

    bu_list = []
    probleme1_counts, probleme2_counts = [], []
    probleme3_counts, probleme4_counts, probleme5_counts = [], [], []

    for bu in bus:
        bu_queryset = base_queryset.filter(id_region__bu=bu)
        p1 = bu_queryset.filter(id_reponse__amelioraion_passif="1").count()
        p2 = bu_queryset.filter(id_reponse__amelioraion_passif="2").count()
        p3 = bu_queryset.filter(id_reponse__amelioraion_passif="3").count()
        p4 = bu_queryset.filter(id_reponse__amelioraion_passif="4").count()
        p5 = bu_queryset.filter(id_reponse__amelioraion_passif="5").count()
        bu_list.append(bu)
        probleme1_counts.append(p1)
        probleme2_counts.append(p2)
        probleme3_counts.append(p3)
        probleme4_counts.append(p4)
        probleme5_counts.append(p5)

    # Compter les réponses pour id_question = 13 avec le même filtre année/semestre
    generale_query = FactTable.objects.filter(
        id_question=13,
        id_reponse__amelioraion_generale__in=["1", "2", "3", "4", "5"]
    )
    if annee_int:
        generale_query = generale_query.filter(id_date__annee=annee_int)
    if filtre1 == '1':
        generale_query = generale_query.filter(id_date__mois__lte=6)
    elif filtre1 == '2':
        generale_query = generale_query.filter(id_date__mois__gte=7)
    resultats_generale = (
        generale_query
        .values('id_reponse__amelioraion_generale')
        .annotate(total=Count('id'))
    )
    amelioraion_generale_counts = {
        row['id_reponse__amelioraion_generale']: row['total']
        for row in resultats_generale
    }

    context = {
        'p1': probleme_counts.get("1", 0),
        'p2': probleme_counts.get("2", 0),
        'p3': probleme_counts.get("3", 0),
        'p4': probleme_counts.get("4", 0),
        'p5': probleme_counts.get("5", 0),
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
        'am1': amelioraion_generale_counts.get("1", 0),
        'am2': amelioraion_generale_counts.get("2", 0),
        'am3': amelioraion_generale_counts.get("3", 0),
        'am4': amelioraion_generale_counts.get("4", 0),
        'am5': amelioraion_generale_counts.get("5", 0),
    }
    return render(request, 'amelioration_home.html', context)