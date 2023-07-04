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
from mega_bazar import valid_contacts
from whatsapp import WhatsApp


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
        gooey_options={"full_width": True},
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

    config["ArquivoContatos"] = args.ArquivoContatos
    config["Imagem"] = args.Imagem
    config["Texto"] = args.Texto

    save_config(config)

    print("Identificando contatos válidos...")
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
                f"Não foi possível enviar a mensagem para '{name}' através do número ({phone}) por conta do erro ({e})"
            )
            # raise e  # for debug
        finally:
            add_progress()

    wpp.stop()


if __name__ == "__main__":
    main()
