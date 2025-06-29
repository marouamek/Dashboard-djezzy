from django.contrib import admin
from .models import ClientReponseSa, DimClient, DimQuestion,DimRegion, DimReponse,FactTable,DimTemps ,CommentaireClient
admin.site.register(DimClient)
admin.site.register(DimQuestion)
admin.site.register(ClientReponseSa)
admin.site.register(DimRegion)
admin.site.register(DimReponse)
admin.site.register(FactTable)
admin.site.register(DimTemps)
admin.site.register(CommentaireClient)

