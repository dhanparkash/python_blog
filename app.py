app = Flask(
    __name__,
    template_folder=os.path.join("main_app","templates"),
    static_folder=os.path.join("main_app","static")
)

app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp)
