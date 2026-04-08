from header import EmailHeader
from body import EmailBody

class EmailMessage:
    """
    A parsed email.

    Attributes
    ----------

    raw_message : email.message.Message
        The raw email message object
    header: EmailHeader
        The header of the email.
    body: EmailBody
        The body of the email
    """
    def __init__(self, msg):
        """
        Constructs an EmailMessage with a raw email.

        Parameters
        ==========
        msg: email.message.Message
            The raw email to parse
        """
        self.raw_message = msg
        self.body: EmailBody = EmailBody(msg)
        self.header: EmailHeader = EmailHeader(msg)


"""
This module contains the implementations for email input functions
"""
import email
import traceback
from email.header import Header
from email.parser import BytesParser
from email import policy
from typing import List, Tuple

import chardet
from tqdm import tqdm

from email.parser import BytesParser
from email import policy
from email.message import EmailMessage
import chardet

def read_email_from_file(file_path: str) -> EmailMessage:
    """
    Reads an email from a file.

    Parameters
    ----------
    file_path: str
        The path of the email to read.

    Returns
    -------
    msg: EmailMessage
        The parsed email.
    """
    with open(file_path, 'rb') as f:
        # Utilisation de BytesParser pour parser le fichier
        msg = BytesParser(policy=policy.default).parse(f)

    try:
        # Vérification des en-têtes et du contenu
        for header in msg:
            if isinstance(msg[header], bytes):  # Vérifie si l'en-tête est en bytes
                msg[header] = msg[header].decode('utf-8', errors='ignore')  # Décode en UTF-8
        for part in msg.walk():
            if not part.is_multipart():
                str(part)  # Convertit le contenu en chaîne de caractères
    except (LookupError, KeyError) as e:
        # Gestion des erreurs de charset ou d'encodage
        print(f"Error parsing email: {e}")
        encoding = chardet.detect(open(file_path, 'rb').read())['encoding']
        if not encoding:
            encoding = 'utf-8'  # Fallback à UTF-8 si l'encodage n'est pas détecté
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            text = f.read()
            msg = email.message_from_string(text)  # Fallback à l'analyse à partir d'une chaîne
    except UnicodeError as e:
        print(f"Unicode error: {e}")
        pass

    return msg  # Retourne directement l'objet EmailMessage
