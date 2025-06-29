from django.shortcuts import render
import json
from satisfaction_client.models import FactTable, DimClient,  LatestResponseCsat , LatestResponseNps,DimTemps
from django.db.models import Count, Case, When, Value, CharField
from django.db.models.functions import Lower


def churn(request):
    # === Récupération des filtres depuis la requête ===
    trimestre_filter = request.GET.get('trimestre')
    periode = request.GET.get('periode')
    mois_range_str = request.GET.get('mois_range')
    trimestre_str = request.GET.get('trimestre_top')
    annees = list(DimTemps.objects.values_list('annee', flat=True).distinct().order_by('-annee'))    


    # === Définition des trimestres et semestres ===
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

    # === Calcul du taux de churn global ===
    total_clients = DimClient.objects.count()
    churned_clients = DimClient.objects.filter(abonne_status__iexact="TER").count()
    churn_rate = (churned_clients / total_clients) * 100 if total_clients > 0 else 0



    non_satisfait = LatestResponseCsat.objects.filter(non_satisfait=1).count()
    is_detracteur = LatestResponseNps.objects.filter(is_detracteur=1).count()


    # === Filtrage des clients 0–3 mois ===
    clients_03 = DimClient.objects.filter(age_client='0-3')

    # === Récupération des entrées détracteurs et non satisfaits pour ces clients ===
    detract_entries = FactTable.objects.filter(is_detracteur=1, id_client__in=clients_03)
    nonsatisfait_entries = FactTable.objects.filter(non_satisfait=1, id_client__in=clients_03)


    # Appliquer le filtre par année si disponible
    annee_str = request.GET.get("annee")  or (str(annees[0]) if annees else '') 
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

    # === Répartition par tranche d’âge de l’abonné ===
    AGE_ABONNE_ORDER = ['18–24', '25–34', '35–44', '45–50', '51–60', '60+', 'Unknown']
    age_distribution = final_results.values('id_client__age_abonne').annotate(total=Count('id'))
    age_map = {item['id_client__age_abonne'] or 'Unknown': item['total'] for item in age_distribution}
    labels_age = AGE_ABONNE_ORDER
    data_age = [age_map.get(age, 0) for age in labels_age]

    # === Répartition par type de client ===
    repartition_type_client = final_results.values('id_client__type_client').annotate(total=Count('id')).order_by('-total')
    labels_type_client = [entry['id_client__type_client'] or 'Unknown' for entry in repartition_type_client]
    data_type_client = [entry['total'] for entry in repartition_type_client]

    # === Regroupement des offres cibles ===
    target_offers = [
        'Newhaylabezzef', 'DJEZZY_HAYLABEZZEF', 'Lowvalue',
        'Mixteprepaid', 'DJEZZY_HAYLAMAXI', 'DjezzyCarte_NEW',
        'Offrejeune', 'Hadraprepaid', 'Individual Hybrid'
    ]

    final_client_ids = final_results.values_list('id_client', flat=True).distinct()

    # === Regroupement des clients par groupe d'offre ===
    clients = DimClient.objects.filter(id_client__in=final_client_ids).annotate(
        offer_group=Case(
            *[When(globale_profile=offer, then=Value(offer)) for offer in target_offers],
            default=Value('Other'),
            output_field=CharField()
        )
    )

    offer_counts = clients.values('offer_group').annotate(count=Count('id_client')).order_by('-count')
    labels_offre = [item['offer_group'] for item in offer_counts]
    data_offre = [item['count'] for item in offer_counts]

    # === Répartition par Business Unit ===
    bu_distribution = (
        final_results
        .values('id_region__bu')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    labels_bu = [entry['id_region__bu'] or 'Unknown' for entry in bu_distribution]
    data_bu = [entry['total'] for entry in bu_distribution]

    # === Répartition des statuts TER/ACT par tranche d’âge abonné ===
    age_status_distribution = (
        DimClient.objects
        .filter(abonne_status__in=['TER', 'ACT'])
        .values('age_abonne', 'abonne_status')
        .annotate(total=Count('id_client'))
    )
    age_status_map = {age: {'TER': 0, 'ACT': 0} for age in AGE_ABONNE_ORDER}
    for entry in age_status_distribution:
        age = entry['age_abonne'] 
        status = entry['abonne_status']
        if age in age_status_map:
            age_status_map[age][status] = entry['total']
    labels_age_status = AGE_ABONNE_ORDER
    data_ter = [age_status_map[age]['TER'] for age in labels_age_status]
    data_act = [age_status_map[age]['ACT'] for age in labels_age_status]




    # === Répartition TER/ACT par type de souscription (type_client) ===

    desired_types = ['individual', 'business', 'unknown']

    type_souscription_distribution = (
        DimClient.objects
        .filter(
            abonne_status__in=['TER', 'ACT'],
        )
        .annotate(normalized_sub=Lower('type_client'))
        .filter(normalized_sub__in=desired_types)  # filtrer seulement les types désirés
        .values('normalized_sub', 'abonne_status')
        .annotate(total=Count('id_client'))
    )

    # Initialiser le dict avec 0 pour tous les types demandés
    souscription_map = {sub: {'TER': 0, 'ACT': 0} for sub in desired_types}

    for entry in type_souscription_distribution:
        sub = entry['normalized_sub']
        status = entry['abonne_status']
        count = entry['total']
        souscription_map[sub][status] = count  # plus de limite

    # Préparer les listes dans l'ordre voulu
    labels_type_abonne = desired_types
    data_ter_abonne = [souscription_map[sub]['TER'] for sub in desired_types]
    data_act_abonne = [souscription_map[sub]['ACT'] for sub in desired_types]






    # === Répartition TER/ACT par offre ===
    # Requête ORM avec regroupement par offre cible ou 'Other'
    grouped = (
        DimClient.objects
        .filter(abonne_status__in=['TER', 'ACT'])
        .annotate(
            profile_group=Case(
                *(When(globale_profile=offer, then=Value(offer)) for offer in target_offers),
                default=Value('Other'),
                output_field=CharField()
            )
        )
        .values('profile_group', 'abonne_status')
        .annotate(total=Count('id_client'))
    )

    # Construction des résultats
    result = {}
    for row in grouped:
        profile = row['profile_group']
        status = row['abonne_status']
        count = row['total']
        if profile not in result:
            result[profile] = {'TER': 0, 'ACT': 0}
        result[profile][status] = count

    # Organisation des données dans l’ordre des labels
    labels2 = list(result.keys())
    data_ter2 = [result[label]['TER'] for label in labels2]
    data_act2 = [result[label]['ACT'] for label in labels2]


    # === Répartition des clients TERMINÉ/ACTIF par tranche d'age ===

    AGE_CLIENT_ORDER = ['0-3', '4-8', '9-12', '13-20', '20+', 'Unknown']

    grouped = (
        DimClient.objects
        .filter(abonne_status__in=['TER', 'ACT'])
        .values('age_client', 'abonne_status')
        .annotate(total=Count('id_client'))
    )

    result = {age: {'TER': 0, 'ACT': 0} for age in AGE_CLIENT_ORDER}

    for row in grouped:
        age = row['age_client']  
        status = row['abonne_status']
        count = row['total']
        if age in result:
            result[age][status] = count

    labels_age_client = AGE_CLIENT_ORDER
    data_ter_age_client = [result[age]['TER'] for age in labels_age_client]
    data_act_age_client = [result[age]['ACT'] for age in labels_age_client]



            # === Préparation du contexte pour le template ===
    context = {
        'churn_rate': round(churn_rate, 2),
        'churn_data_json': json.dumps(churn_data),
        'selected_trimestre': trimestre_filter,
        'selected_periode': periode,
        'selected_mois_range': mois_range_str,
        'selected_trimestre_top': trimestre_str,
        'clients_termines': churned_clients,
        'labels_age': labels_age,
        'data_age': data_age,
        'labels_type_client': labels_type_client,
        'data_type_client': data_type_client,
        'labels_offre': labels_offre,
        'data_offre': data_offre,
        'labels_bu': labels_bu,
        'data_bu': data_bu,
        'labels_age_status': labels_age_status,
        'data_ter': data_ter,
        'data_act': data_act,
        'labels_type_abonne': labels_type_abonne,
        'data_ter_type': data_ter_abonne,
        'data_act_type': data_act_abonne,
        'labels2': labels2,
        'data_ter2': data_ter2,
        'data_act2': data_act2,
        'labels_age_client': labels_age_client,
        'data_ter_age_client': data_ter_age_client,
        'data_act_age_client': data_act_age_client,
        'is_detracteur':is_detracteur,
        'non_satisfait':non_satisfait,
        'annees': annees,

    }

    # === Rendu du template avec les données ===
    return render(request, 'churn.html', context)






