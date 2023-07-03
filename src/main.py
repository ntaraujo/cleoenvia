from gooey import Gooey, GooeyParser, local_resource_path
import signal
from utils import save_config, load_config


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
        "ArquivoContatos", widget="FileChooser", default=config["ArquivoContatos"]
    )
    parser.add_argument("Imagem", widget="FileChooser", default=config["Imagem"])
    # TODO workaround for emoji in the end getting lost
    parser.add_argument("Texto", widget="Textarea", default=config["Texto"])
    args = parser.parse_args()
    
    config["ArquivoContatos"] = args.ArquivoContatos
    config["Imagem"] = args.Imagem
    config["Texto"] = args.Texto
    
    save_config(config)

    print(args.Texto)


if __name__ == "__main__":
    main()
