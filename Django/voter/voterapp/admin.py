from django.contrib import admin
from .models import Voter, Election, Candidate, Vote

admin.site.register(Voter)
admin.site.register(Election)
admin.site.register(Candidate)
admin.site.register(Vote)

