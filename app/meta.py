import tomllib

from pydantic import BaseModel, ConfigDict, Field


class ModelMixin(BaseModel):
    model_config = ConfigDict(extra="allow")


class PyprojectAuthor(ModelMixin):
    name: str


class PyprojectURLs(ModelMixin):
    homepage: str = Field(alias="Homepage")


class PyprojectData(ModelMixin):
    name: str
    version: str
    description: str
    authors: list[PyprojectAuthor]
    urls: PyprojectURLs
    dependencies: list[str]


class AppMetadata(ModelMixin):
    pyproject_data: PyprojectData

    @property
    def name(self):
        return self.pyproject_data.name

    @property
    def version(self):
        return self.pyproject_data.version

    @property
    def description(self):
        return self.pyproject_data.description

    @property
    def author(self):
        return self.pyproject_data.authors[0]

    @property
    def homepage(self):
        return self.pyproject_data.urls.homepage


def get_app_metadata() -> AppMetadata:
    from app.main import APP_DIR

    pyproject_file_path = APP_DIR / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_file_path.read_text())["project"]
    pyproject_data = PyprojectData.model_validate(pyproject_data)
    app_metadata = AppMetadata(pyproject_data=pyproject_data)
    return app_metadata
