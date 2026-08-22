# seances/management/commands/envoyer_rappels.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from seances.models import RappelSeance
from seances.notifications import envoyer_rappel


class Command(BaseCommand):
    help = "Envoie les rappels de séance dus (SMS/WhatsApp)"

    def handle(self, *args, **options):
        maintenant = timezone.now()
        rappels = RappelSeance.objects.filter(
            statut='en_attente',
            date_envoi_prevue__lte=maintenant,
        ).select_related('seance')

        for rappel in rappels:
            try:
                envoyer_rappel(rappel)
                rappel.statut = 'envoye'
                rappel.date_envoi_reelle = maintenant
                self.stdout.write(f"✅ Rappel envoyé : {rappel}")
            except Exception as e:
                rappel.statut = 'echec'
                rappel.erreur = str(e)
                self.stdout.write(self.style.ERROR(f"❌ Échec rappel {rappel.id}: {e}"))
            rappel.save()