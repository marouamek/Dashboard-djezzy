from django.shortcuts import render
from django.db.models import Count, F, Case, When, Value, IntegerField, Sum, Avg
from django.contrib.auth.decorators import login_required
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Q
from django.db.models import CharField
from django.db.models.functions import Cast
from Commentaire.models import CommentaireClient
from satisfaction_client.models import DimTemps
import json
import re
from collections import Counter


  
@login_required(login_url='login_user')

def sentiment_client(request):

    annees = sorted(DimTemps.objects.values_list('annee', flat=True).distinct())
    annee_selectionnee = request.GET.get('annee') or (annees[-1] if annees else None)
    annee_int = int(annee_selectionnee)
    filtre1 = request.GET.get("mois")


    total_commentaires = CommentaireClient.objects.exclude(commentaire__isnull=True).exclude(commentaire__exact='').count()
    annees = DimTemps.objects.values_list('annee', flat=True).distinct().order_by('-annee')
    filtre1 = request.GET.get("mois")
    annee_str = request.GET.get("annee")
    #RESEAUX
    filtre2 = request.GET.get("mois")
    annee_str2 = request.GET.get("annee")
    # SERVICE CLIENT
    filtre3 = request.GET.get("mois")
    annee_str3 = request.GET.get("annee")
    #PRIX ET TARIFICATION
    filtre4 = request.GET.get("mois")
    annee_str4 = request.GET.get("annee")
    #OFFRE ET SERVICE
    filtre5 = request.GET.get("mois")
    annee_str5 = request.GET.get("annee")
     #AUTRE
    filtre6 = request.GET.get("mois")
    annee_str6 = request.GET.get("annee")



    # Nombre par sentiment
    stats = (
        CommentaireClient.objects
        .values('sentiment')
        .annotate(count=Count('sentiment'))
    )

    # Initialisation
    nb_positifs = nb_negatifs = nb_neutres = 0

    for stat in stats:
        sentiment = stat['sentiment'].lower()
        if sentiment == 'positif':
            nb_positifs = stat['count']
        elif sentiment == 'négatif' or sentiment == 'negatif':
            nb_negatifs = stat['count']
        elif sentiment == 'neutre':
            nb_neutres = stat['count']

    # Calcul des taux avec protection contre division par zéro
    taux_positifs = (nb_positifs / total_commentaires) * 100 if total_commentaires else 0
    taux_negatifs = (nb_negatifs / total_commentaires) * 100 if total_commentaires else 0
    taux_neutres = (nb_neutres / total_commentaires) * 100 if total_commentaires else 0


    #_______________________________________________________________________#
    

    base_query = CommentaireClient.objects.filter(
        theme__iexact="internet"
    ).exclude(commentaire__isnull=True).exclude(commentaire='').annotate(
        annee=ExtractYear('survey_date'),
        mois=ExtractMonth('survey_date')
    )
    if annee_int:
        base_query = base_query.filter(annee=annee_int)
    if filtre1 == '1':
        base_query = base_query.filter(mois__lte=6)
    elif filtre1 == '2':
        base_query = base_query.filter(mois__gte=7)

    qs_pos = base_query.filter(sentiment__iexact="positif").values(label=F('mois')).annotate(nb=Count('sentiment')).order_by('label')
    qs_neg = base_query.filter(sentiment__iexact="negatif").values(label=F('mois')).annotate(nb=Count('sentiment')).order_by('label')
    qs_neu = base_query.filter(sentiment__iexact="neutre").values(label=F('mois')).annotate(nb=Count('sentiment')).order_by('label')

    mois_set = set()
    for qs in [qs_pos, qs_neg, qs_neu]:
        for item in qs:
            mois_set.add(f"{int(item['label']):02d}")
    liste_mois = sorted(mois_set)

    def qs_to_dict(qs):
        return {f"{int(item['label']):02d}": item['nb'] for item in qs}
    dict_pos = qs_to_dict(qs_pos)
    dict_neg = qs_to_dict(qs_neg)
    dict_neu = qs_to_dict(qs_neu)
    def build_count_list(d):
        return [d.get(m, 0) for m in liste_mois]
    nombre_pos = build_count_list(dict_pos)
    nombre_neg = build_count_list(dict_neg)
    nombre_neu = build_count_list(dict_neu)


   #RESEAUX _____________________________________________________________#


    query_appel = CommentaireClient.objects.filter(
        theme__iexact="appel"
    ).exclude(commentaire__isnull=True).exclude(commentaire='')

    query_appel = query_appel.annotate(annee=ExtractYear('survey_date'))

    if annee_str2:
        try:
            annee_int = int(annee_str2)
            query_appel = query_appel.filter(annee=annee_int)
        except ValueError:
            pass

    query_appel = query_appel.annotate(mois_appel=ExtractMonth('survey_date'))

    if filtre2 == '1':
        query_appel = query_appel.filter(mois_appel__lte=6)
    elif filtre2 == '2':
        query_appel = query_appel.filter(mois_appel__gte=7)

    qs_positifs = query_appel.filter(sentiment__iexact="positif").values(label=F('mois_appel')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_negatifs = query_appel.filter(sentiment__iexact="negatif").values(label=F('mois_appel')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_neutres = query_appel.filter(sentiment__iexact="neutre").values(label=F('mois_appel')).annotate(nombre=Count('sentiment')).order_by('label')

    mois_set_appel = set()
    for qs in [qs_positifs, qs_negatifs, qs_neutres]:
        for item in qs:
            mois_set_appel.add(f"{int(item['label']):02d}")
    liste_mois_appel = sorted(mois_set_appel)

    def qs_to_dict(qs):
        return {f"{int(item['label']):02d}": item['nombre'] for item in qs}

    dict_positifs = qs_to_dict(qs_positifs)
    dict_negatifs = qs_to_dict(qs_negatifs)
    dict_neutres = qs_to_dict(qs_neutres)

    def build_count_list(d):
        return [d.get(m, 0) for m in liste_mois_appel]

    nombres_positifs_appel = build_count_list(dict_positifs)
    nombres_negatifs_appel = build_count_list(dict_negatifs)
    nombres_neutres_appel = build_count_list(dict_neutres)

   # SERVICE CLIENT _____________________________________#
    query_service = CommentaireClient.objects.filter(
        theme__iexact="service client"
    ).exclude(commentaire__isnull=True).exclude(commentaire='')

    query_service = query_service.annotate(annee=ExtractYear('survey_date'))

    if annee_str3:
        try:
            annee_int = int(annee_str3)
            query_service = query_service.filter(annee=annee_int)
        except ValueError:
            pass

    query_service = query_service.annotate(mois_service=ExtractMonth('survey_date'))

    if filtre3 == '1':
        query_service = query_service.filter(mois_service__lte=6)
    elif filtre3 == '2':
        query_service = query_service.filter(mois_service__gte=7)

    qs_positifs = query_service.filter(sentiment__iexact="positif").values(label=F('mois_service')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_negatifs = query_service.filter(sentiment__iexact="negatif").values(label=F('mois_service')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_neutres = query_service.filter(sentiment__iexact="neutre").values(label=F('mois_service')).annotate(nombre=Count('sentiment')).order_by('label')

    mois_set_service = set()
    for qs in [qs_positifs, qs_negatifs, qs_neutres]:
        for item in qs:
            mois_set_service.add(f"{int(item['label']):02d}")
    liste_mois_service = sorted(mois_set_service)

    def qs_to_dict(qs):
        return {f"{int(item['label']):02d}": item['nombre'] for item in qs}

    dict_positifs = qs_to_dict(qs_positifs)
    dict_negatifs = qs_to_dict(qs_negatifs)
    dict_neutres = qs_to_dict(qs_neutres)

    def build_count_list(d):
        return [d.get(m, 0) for m in liste_mois_service]

    nombres_positifs_service = build_count_list(dict_positifs)
    nombres_negatifs_service = build_count_list(dict_negatifs)
    nombres_neutres_service = build_count_list(dict_neutres)

    # PRIX ET TARIFICATION __________________________________________#
    query_prix = CommentaireClient.objects.filter(
        theme__iexact="prix et tarification"
    ).exclude(commentaire__isnull=True).exclude(commentaire='')

    query_prix = query_prix.annotate(annee=ExtractYear('survey_date'))

    if annee_str4:
        try:
            annee_int = int(annee_str4)
            query_prix = query_prix.filter(annee=annee_int)
        except ValueError:
            pass

    query_prix = query_prix.annotate(mois_prix=ExtractMonth('survey_date'))

    if filtre4 == '1':
        query_prix = query_prix.filter(mois_prix__lte=6)
    elif filtre4 == '2':
        query_prix = query_prix.filter(mois_prix__gte=7)

    qs_positifs = query_prix.filter(sentiment__iexact="positif").values(label=F('mois_prix')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_negatifs = query_prix.filter(sentiment__iexact="negatif").values(label=F('mois_prix')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_neutres = query_prix.filter(sentiment__iexact="neutre").values(label=F('mois_prix')).annotate(nombre=Count('sentiment')).order_by('label')

    mois_set_prix = set()
    for qs in [qs_positifs, qs_negatifs, qs_neutres]:
        for item in qs:
            mois_set_prix.add(f"{int(item['label']):02d}")
    liste_mois_prix = sorted(mois_set_prix)

    def qs_to_dict(qs):
        return {f"{int(item['label']):02d}": item['nombre'] for item in qs}

    dict_positifs = qs_to_dict(qs_positifs)
    dict_negatifs = qs_to_dict(qs_negatifs)
    dict_neutres = qs_to_dict(qs_neutres)

    def build_count_list(d):
        return [d.get(m, 0) for m in liste_mois_prix]

    nombres_positifs_prix = build_count_list(dict_positifs)
    nombres_negatifs_prix = build_count_list(dict_negatifs)
    nombres_neutres_prix = build_count_list(dict_neutres)

    #_________________________________________________________________________#

    query_offre = CommentaireClient.objects.filter(
        theme__iexact="offre et service"
    ).exclude(commentaire__isnull=True).exclude(commentaire='')

    query_offre = query_offre.annotate(annee=ExtractYear('survey_date'))

    if annee_str5:
        try:
            annee_int = int(annee_str5)
            query_offre = query_offre.filter(annee=annee_int)
        except ValueError:
            pass

    query_offre = query_offre.annotate(mois_offre=ExtractMonth('survey_date'))

    if filtre5 == '1':
        query_offre = query_offre.filter(mois_offre__lte=6)
    elif filtre5 == '2':
        query_offre = query_offre.filter(mois_offre__gte=7)

    qs_positifs = query_offre.filter(sentiment__iexact="positif").values(label=F('mois_offre')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_negatifs = query_offre.filter(sentiment__iexact="negatif").values(label=F('mois_offre')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_neutres = query_offre.filter(sentiment__iexact="neutre").values(label=F('mois_offre')).annotate(nombre=Count('sentiment')).order_by('label')

    mois_set_offre = set()
    for qs in [qs_positifs, qs_negatifs, qs_neutres]:
        for item in qs:
            mois_set_offre.add(f"{int(item['label']):02d}")
    liste_mois_offre = sorted(mois_set_offre)

    def qs_to_dict(qs):
        return {f"{int(item['label']):02d}": item['nombre'] for item in qs}

    dict_positifs = qs_to_dict(qs_positifs)
    dict_negatifs = qs_to_dict(qs_negatifs)
    dict_neutres = qs_to_dict(qs_neutres)

    def build_count_list(d):
        return [d.get(m, 0) for m in liste_mois_offre]

    nombres_positifs_offre = build_count_list(dict_positifs)
    nombres_negatifs_offre = build_count_list(dict_negatifs)
    nombres_neutres_offre = build_count_list(dict_neutres)


#_________________AUTRE___________________________#


    query_autre = CommentaireClient.objects.filter(
        theme__iexact="autre"
    ).exclude(commentaire__isnull=True).exclude(commentaire='')

    query_autre = query_autre.annotate(annee=ExtractYear('survey_date'))

    if annee_str6:
        try:
            annee_int = int(annee_str6)
            query_autre = query_autre.filter(annee=annee_int)
        except ValueError:
            pass

    query_autre = query_autre.annotate(mois_autre=ExtractMonth('survey_date'))

    if filtre6 == '1':
        query_autre = query_autre.filter(mois_autre__lte=6)
    elif filtre6 == '2':
        query_autre = query_autre.filter(mois_autre__gte=7)

    qs_positifs = query_autre.filter(sentiment__iexact="positif").values(label=F('mois_autre')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_negatifs = query_autre.filter(sentiment__iexact="negatif").values(label=F('mois_autre')).annotate(nombre=Count('sentiment')).order_by('label')
    qs_neutres = query_autre.filter(sentiment__iexact="neutre").values(label=F('mois_autre')).annotate(nombre=Count('sentiment')).order_by('label')

    mois_set_autre = set()
    for qs in [qs_positifs, qs_negatifs, qs_neutres]:
        for item in qs:
            mois_set_autre.add(f"{int(item['label']):02d}")
    liste_mois_autre = sorted(mois_set_autre)

    def qs_to_dict(qs):
        return {f"{int(item['label']):02d}": item['nombre'] for item in qs}

    dict_positifs = qs_to_dict(qs_positifs)
    dict_negatifs = qs_to_dict(qs_negatifs)
    dict_neutres = qs_to_dict(qs_neutres)

    def build_count_list(d):
        return [d.get(m, 0) for m in liste_mois_autre]

    nombres_positifs_autre = build_count_list(dict_positifs)
    nombres_negatifs_autre = build_count_list(dict_negatifs)
    nombres_neutres_autre = build_count_list(dict_neutres)



    # Filtre de base pour les commentaires
    commentaire_filter = {'survey_date__year': annee_int}
    if filtre1 == '1':
        commentaire_filter['survey_date__month__lte'] = 6
    elif filtre1 == '2':
        commentaire_filter['survey_date__month__gte'] = 7

    qs = CommentaireClient.objects.filter(**commentaire_filter).annotate(
        sentiment_score=Case(
            When(sentiment__iexact="positif", then=Value(1)),
            When(sentiment__iexact="negatif", then=Value(-1)),
            When(sentiment__iexact="neutre", then=Value(0)),
            default=Value(0),
            output_field=IntegerField()
        )
    )

    agg = qs.aggregate(
        total_score=Sum('sentiment_score'),
        total_commentaires=Count('sentiment')
    )

    score_moyen = 0
    if agg['total_commentaires'] > 0:
        score_moyen = (agg['total_score'] / agg['total_commentaires']) * 100

    # Promoteurs
    promoteurs_qs = CommentaireClient.objects.filter(
        nps__regex=r'^\d+$',
        **commentaire_filter
    ).annotate(
        nps_int=Cast('nps', IntegerField())
    ).filter(nps_int__gte=9, nps_int__lte=10)

    total_promoteurs = promoteurs_qs.count()
    nb_positifs = promoteurs_qs.filter(sentiment__iexact="positif").count()

    pourcentage_positif_promoteurs = 0
    if total_promoteurs > 0:
        pourcentage_positif_promoteurs = (nb_positifs / total_promoteurs) * 100

    # Détracteurs
    detracteurs_qs = CommentaireClient.objects.filter(
        nps__regex=r'^\d+$',
        **commentaire_filter
    ).annotate(
        nps_int=Cast('nps', IntegerField())
    ).filter(nps_int__gte=0, nps_int__lte=6)

    total_detracteurs = detracteurs_qs.count()
    nb_negatifs = detracteurs_qs.filter(sentiment__iexact="negatif").count()

    pourcentage_negatif_detracteurs = 0
    if total_detracteurs > 0:
        pourcentage_negatif_detracteurs = (nb_negatifs / total_detracteurs) * 100

    # Score NPS moyen
    qs = CommentaireClient.objects.filter(
        nps__regex=r'^\d+$',
        **commentaire_filter
    ).annotate(
        nps_int=Cast('nps', IntegerField()),
        sentiment_nps=Case(
            When(nps_int__gte=9, then=Value(1)),
            When(nps_int__gte=7, nps_int__lte=8, then=Value(0)),
            When(nps_int__lte=6, then=Value(-1)),
            default=Value(0),
            output_field=IntegerField()
        )
    )

    moyenne_score_sentiment = qs.aggregate(moyenne=Avg('sentiment_nps'))['moyenne'] or 0
    moyenne_score_sentiment = round(moyenne_score_sentiment * 100, 2)

    # Inconsistants
    total_nps_match = CommentaireClient.objects.filter(**commentaire_filter).exclude(nps_match__isnull=True).exclude(nps_match__iexact='').count()
    nb_inconsistants = CommentaireClient.objects.filter(nps_match__iexact='false', **commentaire_filter).count()
    pourcentage_inconsistants = round((nb_inconsistants / total_nps_match) * 100, 2) if total_nps_match > 0 else 0




    commentaires = CommentaireClient.objects.exclude(commentaire__isnull=True).values_list('commentaire', flat=True)

    stop_words = set([
    'a', 'à', 'â', 'abord', 'afin', 'ah', 'ai', 'aie', 'ainsi', 'allaient', 'allo', 'allô', 'allons', 'après', 'assez',
    'attendu', 'au', 'aucun', 'aucune', 'aujourdhui', 'aupres', 'aupres', 'auquel', 'aura', 'auront', 'aussi',
    'autre', 'autres', 'aux', 'auxquelles', 'auxquels', 'avaient', 'avais', 'avait', 'avant', 'avec', 'avoir', 'ayant',
    'b', 'bah', 'bas', 'basee', 'bat', 'beaucoup', 'bien', 'bigre', 'boum', 'bravo', 'brrr', 'c', 'ça', 'car', 'ce', 'ceci',
    'cela', 'celle', 'celleci', 'cellela', 'celles', 'cellesci', 'cellesla', 'celui', 'celuici', 'celuila', 'cent',
    'cependant', 'certain', 'certaine', 'certaines', 'certains', 'certes', 'ces', 'cet', 'cette', 'ceux', 'ceuxci', 'ceuxla',
    'chacun', 'chaque', 'cher', 'chere', 'cheres', 'chers', 'chez', 'chiche', 'chut', 'ci', 'cinq', 'cinquantaine', 'cinquante',
    'cinquantieme', 'cinquieme', 'clac', 'clic', 'combien', 'comme', 'comment', 'compris', 'concernant', 'contre', 'couic',
    'crac', 'd', 'da', 'dans', 'de', 'debout', 'dedans', 'dehors', 'dela', 'depuis', 'dernier', 'derniere', 'derriere', 'des',
    'desormais', 'desquelles', 'desquels', 'dessous', 'dessus', 'deux', 'deuxieme', 'deuxiemement', 'devant', 'devers',
    'devra', 'different', 'differente', 'differentes', 'differents', 'dire', 'divers', 'diverse', 'diverses', 'dix', 'dixhuit',
    'dixieme', 'dixneuf', 'dixsept', 'doit', 'doivent', 'donc', 'dont', 'douze', 'douzieme', 'dring', 'du', 'duquel', 'durant',
    'e', 'effet', 'eh', 'elle', 'ellememe', 'elles', 'ellesmemes', 'en', 'encore', 'entre', 'envers', 'environ', 'es', 'es',
    'est', 'et', 'etant', 'etaient', 'etais', 'etait', 'etant', 'etc', 'ete', 'etre', 'etre', 'eu', 'euh', 'eux', 'euxmemes',
    'excepte', 'f', 'facon', 'fais', 'faisaient', 'faisant', 'fait', 'feront', 'fi', 'flac', 'floc', 'font', 'g', 'gens', 'h',
    'ha', 'he', 'hein', 'helas', 'hem', 'hep', 'hi', 'ho', 'hola', 'hop', 'hormis', 'hors', 'hou', 'houp', 'hue', 'hui', 'huit',
    'huitieme', 'hum', 'hurrah', 'i', 'il', 'ils', 'importe', 'j', 'je', 'jusqu', 'jusque', 'k', 'l', 'la', 'la', 'laquelle',
    'las', 'le', 'lequel', 'les', 'les', 'lesquelles', 'lesquels', 'leur', 'leurs', 'longtemps', 'lors', 'lorsque', 'lui',
    'luimeme', 'm', 'ma', 'maint', 'mais', 'malgre', 'me', 'meme', 'memes', 'merci', 'mes', 'mien', 'mienne', 'miennes',
    'miens', 'mille', 'mince', 'moi', 'moimeme', 'moins', 'mon', 'moyennant', 'n', 'na', 'ne', 'neanmoins', 'ni', 'nombreuses',
    'nombreux', 'non', 'nos', 'notre', 'notre', 'notres', 'nous', 'nousmemes', 'nul', 'o', 'o', 'oh', 'ohe', 'ole', 'olle',
    'on', 'ont', 'onze', 'onzieme', 'ore', 'ou', 'ou', 'ouf', 'ouias', 'oust', 'ouste', 'outre', 'p', 'paf', 'pan', 'par',
    'parmi', 'partant', 'particulier', 'particuliere', 'particulierement', 'pas', 'passe', 'pendant', 'personne', 'peu',
    'peut', 'peuvent', 'peux', 'pff', 'pfft', 'pfut', 'pif', 'plein', 'plouf', 'plus', 'plusieurs', 'plutot', 'pouah', 'pour',
    'pourquoi', 'premier', 'premiere', 'premierement', 'pres', 'proche', 'psitt', 'puis', 'puisque', 'q', 'qu', 'quand',
    'quant', 'quanta', 'quarante', 'quatorze', 'quatre', 'quatrevingt', 'quatrieme', 'quatriemement', 'que', 'quel',
    'quelconque', 'quelle', 'quelles', 'quelquun', 'quelque', 'quelques', 'quels', 'qui', 'quiconque', 'quinze', 'quoi',
    'quoique', 'r', 'revoici', 'revoila', 'rien', 's', 'sa', 'sacrebleu', 'sans', 'sapristi', 'sauf', 'se', 'seize', 'selon',
    'sept', 'septieme', 'sera', 'seront', 'ses', 'si', 'sien', 'sienne', 'siennes', 'siens', 'sinon', 'six', 'sixieme', 'soi',
    'soimeme', 'soit', 'soixante', 'son', 'sont', 'sous', 'stop', 'suis', 'suivant', 'sur', 'surtout', 't', 'ta', 'tac', 'tant',
    'te', 'te', 'tel', 'telle', 'tellement', 'telles', 'tels', 'tenant', 'tes', 'tic', 'tien', 'tienne', 'tiennes', 'tiens',
    'toc', 'toi', 'toimeme', 'ton', 'touchant', 'toujours', 'tous', 'tout', 'toute', 'toutes', 'treize', 'trente', 'tres',
    'trois', 'troisieme', 'troisiemement', 'tu', 'u', 'un', 'une', 'unes', 'uns', 'v', 'va', 'vais', 'vas', 've', 'vers', 'via',
    'vif', 'vifs', 'vingt', 'vivat', 'vive', 'vives', 'voici', 'voila', 'vont', 'vos', 'votre', 'votre', 'votres', 'vous',
    'vousmemes', 'vu', 'w', 'x', 'y', 'z', 'zut', 'cest',
    # Formes du verbe "avoir"
    'jai', 'as', 'a', 'avons', 'avez', 'ont', 'avais', 'avait', 'avions', 'aviez', 'avaient',
    'eus', 'eut', 'eumes', 'eutes', 'eurent', 'aurai', 'auras', 'aura', 'aurons', 'aurez', 'auront',
    'aurais', 'aurait', 'aurions', 'auriez', 'auraient', 'eusse', 'eusses', 'eut', 'eussions', 'eussiez', 'eussent',
    'ayant', 'eu', 'eue', 'eus', 'eues', 'avoir',
    # Formes du verbe "etre"
    'suis', 'es', 'est', 'sommes', 'etes', 'sont', 'etais', 'etait', 'etions', 'etiez', 'etaient',
    'fus', 'fut', 'fumes', 'futes', 'furent', 'serai', 'seras', 'sera', 'serons', 'serez', 'seront',
    'serais', 'serait', 'serions', 'seriez', 'seraient', 'fusse', 'fusses', 'fut', 'fussions', 'fussiez', 'fussent',
    'etant', 'ete', 'etre', 'nai','même','été','était','très','était' ])

    tous_les_mots = []
    for commentaire in commentaires:
        text = commentaire.lower()
        text = re.sub(r'[^\w\s]', '', text)
        mots = text.split()
        mots_filtrés = [mot for mot in mots if mot not in stop_words and len(mot) > 2]
        tous_les_mots.extend(mots_filtrés)

    freq = Counter(tous_les_mots).most_common(100)
    mots_js = json.dumps([{"key": mot, "value": count} for mot, count in freq])  # <-- use json.dumps

    mots_js = "[" + ",".join(
        [f'{{key: "{mot}", value: {count}}}' for mot, count in freq]
    ) + "]"



    context = {
        'total_commentaires': total_commentaires,
        'taux_positifs': round(taux_positifs, 2),
        'taux_negatifs': round(taux_negatifs, 2),
        'taux_neutres': round(taux_neutres, 2),
        'annees': annees,

        'mois': liste_mois,
        'nb_positif': nombre_pos,
        'nb_negatif': nombre_neg,
        'nb_neutre': nombre_neu,

        'liste_mois_appel': liste_mois_appel,
        'nb_positifs_appel': nombres_positifs_appel,
        'nb_negatifs_appel': nombres_negatifs_appel,
        'nb_neutres_appel': nombres_neutres_appel,

        'liste_mois_service': liste_mois_service,
        'nb_positifs_service': nombres_positifs_service,
        'nb_negatifs_service': nombres_negatifs_service,
        'nb_neutres_service': nombres_neutres_service,

        'liste_mois_prix': liste_mois_prix,
        'nb_positifs_prix': nombres_positifs_prix,
        'nb_negatifs_prix': nombres_negatifs_prix,
        'nb_neutres_prix': nombres_neutres_prix,

        'liste_mois_offre': liste_mois_offre,
        'nb_positifs_offre': nombres_positifs_offre,
        'nb_negatifs_offre': nombres_negatifs_offre,
        'nb_neutres_offre': nombres_neutres_offre,

        'liste_mois_autre': liste_mois_autre,
        'nb_positifs_autre': nombres_positifs_autre,
        'nb_negatifs_autre': nombres_negatifs_autre,
        'nb_neutres_autre': nombres_neutres_autre,
 
        'pourcentage_sentiment': round(score_moyen, 2),
        'pourcentage_positif_promoteurs': round(pourcentage_positif_promoteurs, 2),
        'pourcentage_negatif_detracteurs': round(pourcentage_negatif_detracteurs, 2),
        'moyenne_score_sentiment' : moyenne_score_sentiment,
        'pourcentage_inconsistants':pourcentage_inconsistants,
        "mots_js": mots_js


        

    }   
    return render(request, 'sentiment_client.html',context)


