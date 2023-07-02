from gooey import Gooey, GooeyParser, local_resource_path
import signal


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
    parser = GooeyParser(description="Vamos enviar sua mensagem ( ＾◡＾ )")
    args = parser.parse_args()

    print("Código aqui")


if __name__ == "__main__":
    main()
