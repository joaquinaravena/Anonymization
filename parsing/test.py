from parsing.header import EmailHeader
from parsing.body import EmailBody
import glob
from email import policy
from email.parser import BytesParser
import random

# parsing d'un mail de signal spam

def parsing_email(email_path):

    #email_message = read_email_from_file(email_path)
    with open(email_path,'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    header = EmailHeader(msg)
    body = EmailBody(msg)
    # Headers attributes
    headers = {"orig_date": header.orig_date,"x_priority": header.x_priority,
             "subject": header.subject,"return_path": header.return_path,
             "reply_to": header.reply_to,"sender_full": header.sender_full,
             "sender_name": header.sender_name,"sender_email_address": header.sender_email_address,
             "to": header.to, "recipient_full": header.recipient_full,
             "recipient_name": header.recipient_name,"recipient_email_address": header.recipient_email_address,
             "message_id": header.message_id,"x_mailer": header.x_mailer,
             "x_originating_hostname": header.x_originating_hostname,"x_originating_ip": header.x_originating_ip,
             "x_virus_scanned":header.x_virus_scanned,"dkim_signed": header.dkim_signed,
             "received_spf": header.received_spf,
             "x_original_authentication_results": header.x_original_authentication_results,
             "received": header.received,"mime_version": header.mime_version
            }
    
    #print(f"Headers Attributes: \n {headers.keys()} \n")
    # Body attributes
    body = {"is_html": body.is_html,"num_attachment":body.num_attachment,
            "content_disposition_list":body.content_disposition_list,"content_type_list":body.content_type_list,
            "content_transfer_encoding_list":body.content_transfer_encoding_list,
            "file_extension_list":body.file_extension_list,"charset_list":body.charset_list,
            "text": body.text,"raw_html": body.raw_html,"html": body.html
           }
    return (headers, body)

# parsing
data_dir = "./data/signal_spam_parsed/"
#file_path = random.choice(glob.glob(f"{data_dir}/*"))

#data_dir = "./data/signalspam/txts/spams"
#file_path = f"{data_dir}/message_2.txt"
#file_path = glob.glob("../eml_folder/*.eml")[0]
file_path = data_dir + "spams/9105"
print(f"{file_path}\n\n")

# champs des en-têtes et du body
(headers, body) = parsing_email(file_path) #file_path
print("HEADERS... \n")
for k,v in headers.items():
  print(f"{k :-<50} {v}")

print("\n\nBODY... \n")
for k,v in body.items():
  print(f"{k :-<50} {v}")