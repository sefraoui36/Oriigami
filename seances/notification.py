# seances/notifications.py
import logging
from twilio.rest import Client as TwilioClient
from django.conf import settings
import re
logger = logging.getLogger(__name__)


def _client():
    return TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def envoyer_rappel_sms(telephone, message):
    _client().messages.create(
        body=message,
        from_=settings.TWILIO_SMS_FROM,
        to=telephone,
    )


def envoyer_rappel_whatsapp(telephone, message):
    numero = normaliser_numero_maroc(telephone)
    if not numero:
        raise ValueError(f"Numéro de téléphone invalide pour l'envoi WhatsApp: {telephone}")
    _client().messages.create(
        body=message,
        from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
        to=f"whatsapp:{numero}",
    )


def construire_message_rappel(seance):
    return (
        f"Rappel Origami Privé : vous avez une séance de {seance.type_seance} "
        f"le {seance.date.strftime('%d/%m/%Y')} à {seance.heure.strftime('%Hh%M')}. "
        f"À bientôt !"
    )


def envoyer_rappel(rappel):
    """Envoie le rappel et met à jour son statut. Lève une exception en cas d'échec."""
    message = construire_message_rappel(rappel.seance)
    if rappel.canal == 'whatsapp':
        envoyer_rappel_whatsapp(rappel.telephone, message)
    else:
        envoyer_rappel_sms(rappel.telephone, message)
def normaliser_numero_maroc(numero):
    """
    Convertit un numéro marocain local vers le format E.164.
    '0612345678' -> '+212612345678'
    '06 12 34 56 78' -> '+212612345678'
    '+212612345678' -> inchangé
    Retourne None si le numéro est invalide (trop court/vide).
    """
    if not numero:
        return None
    chiffres = re.sub(r'\D', '', numero)  # garde uniquement les chiffres

    if numero.strip().startswith('+'):
        return '+' + chiffres

    if chiffres.startswith('212'):
        return '+' + chiffres

    if chiffres.startswith('0') and len(chiffres) == 10:
        return '+212' + chiffres[1:]

    return None        