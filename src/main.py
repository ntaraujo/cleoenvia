from gooey import Gooey, GooeyParser, local_resource_path
import signal
from utils import (
    save_config,
    load_config,
    save_cache,
    load_cache,
    add_total,
    add_progress,
)
from contacts import filtered_contacts, valid_contacts
from whatsapp import WhatsApp
import time


@Gooey(
    language="portuguese",
    program_name="Cleo Envia",
    image_dir=local_resource_path("gooey-images"),
    language_dir=local_resource_path("gooey-languages"),
    show_success_modal=False,
    shutdown_signal=signal.SIGTERM,
    clear_before_run=True,
    progress_regex=r"^Progress: (?P<current>\d+)/(?P<total>\d+)$",
    progress_expr="current / total * 100",
    hide_progress_msg=True,
    # navigation="SIDEBAR",
    # sidebar_title="Ações",
    # show_sidebar=True,
    # advanced=True,
    # tabbed_groups=True,
    timing_options={
        "show_time_remaining": True,
        "hide_time_remaining_on_complete": False,
    },
)
def main():
    config = load_config()

    parser = GooeyParser(description="Vamos enviar sua mensagem ( ＾◡＾ )")
    parser.add_argument(
        "ArquivoContatos",
        widget="FileChooser",
        default=config["ArquivoContatos"],
        help="Arquivo CSV com os contatos do Google",
    )
    parser.add_argument(
        "Incluir",
        widget="FileChooser",
        default=config["Incluir"],
        help="Arquivo com os nomes que você deseja incluir, separados por linha",
    )
    parser.add_argument(
        "Imagem",
        widget="FileChooser",
        default=config["Imagem"],
        help="A imagem que você deseja enviar",
    )
    # TODO workaround for emoji in the end getting lost
    parser.add_argument(
        "Texto",
        widget="FileChooser",
        default=config["Texto"],
        help="O arquivo com o texto que você deseja enviar como descrição da imagem",
    )
    parser.add_argument(
        "Continuação",
        choices=["Sim", "Não"],
        default="Não",
        help="Marque esse campo se deseja continuar de onde parou a última execução",
    )
    parser.add_argument(
        "TentarErrados",
        choices=["Sim", "Não"],
        default="Não",
        help="Marque esse campo se deseja tentar os números que já falharam alguma vez",
    )
    args = parser.parse_args()

    from version import version
    from packaging.version import parse as version_parse
    import requests

    try:
        response = requests.get(
            "https://raw.githubusercontent.com/ntaraujo/cleoenvia/main/public.json",
            verify=False,
        )
        response.raise_for_status()
        public_data = response.json()

    except Exception as e:
        print(
            "Ocorreu um erro ao checar a versão do aplicativo. Por favor verifique se você está conectado à internet, feche o aplicativo e abra-o de novo."
        )
        raise e

    if version_parse(version) < version_parse(public_data["min_version"]):
        raise Exception(  # sourcery skip: raise-specific-error
            "Essa versão do aplicativo não é mais suportada. Por gentileza, entre em contato com o desenvolvedor para obter a versão mais recente."
        )

    config["ArquivoContatos"] = args.ArquivoContatos
    config["Incluir"] = args.Incluir
    config["Imagem"] = args.Imagem
    config["Texto"] = args.Texto

    save_config(config)

    print("Identificando contatos válidos...")
    if args.Incluir:
        contacts = filtered_contacts(args.ArquivoContatos, args.Incluir)
    else:
        contacts = valid_contacts(args.ArquivoContatos)

    print("Abrindo o WhatsApp...")
    wpp = WhatsApp()

    wpp.start()

    wpp.set_image_data(args.Imagem)
    with open(args.Texto, "r", encoding="utf-8") as f:
        text = f.read()

    sent_contact_names = load_cache("sent_contact_names", set())
    continuation = args.Continuação == "Sim"
    if continuation:
        print(
            "Os seguintes contatos tiveram mensagens enviadas na última execução e não serão considerados nesta: (",
            ", ".join(sent_contact_names),
            ")",
        )
    else:
        sent_contact_names = set()
        save_cache("sent_contact_names", sent_contact_names)

    failed_contact_phones = load_cache("failed_contact_phones", set())
    try_wrong = args.TentarErrados == "Sim"
    if try_wrong:
        print(
            "Os seguintes números falharam em alguma execução e serão considerados novamente: (",
            ", ".join(failed_contact_phones),
            ")",
        )
        failed_contact_phones = set()
        save_cache("failed_contact_phones", failed_contact_phones)

    print("Calculando total de mensagens a serem enviadas...")
    planned_recipients = [
        (name, phone)
        for contact in contacts
        for phone in contact["phones"]
        if (name := contact["name"]) not in sent_contact_names
        and phone not in failed_contact_phones
    ]

    add_total(len(planned_recipients))

    # TODO prevent windows sleep
    for name, phone in planned_recipients:
        if name in sent_contact_names:
            add_progress()
            continue

        print(f"Enviando para '{name}' ({phone})")
        try:
            wpp.do_all_send_image(name, phone, text)
            sent_contact_names.add(name)
            save_cache("sent_contact_names", sent_contact_names)
            print(f"Mensagem enviada para '{name}' através do número ({phone})")
        except Exception as e:
            failed_contact_phones.add(phone)
            save_cache("failed_contact_phones", failed_contact_phones)
            print(
                f"Não foi possível enviar a mensagem para '{name}' através do número ({phone}) por conta do erro {type(e).__name__}(\"{str(e).ljust(10, '.')[:min(len(str(e)), 10)]}...\")"
            )
            # raise e  # for debug
        finally:
            add_progress()

    time.sleep(15)
    wpp.stop()


if __name__ == "__main__":
    main()
