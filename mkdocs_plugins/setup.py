from setuptools import find_packages, setup

setup(
    name="mkdocs-schema-docs",
    version="1.0.0",
    description="MkDocs plugin for interactive schema documentation",
    packages=find_packages(),
    entry_points={
        "mkdocs.plugins": [
            "schema_docs = schema_docs.plugin:SchemaDocsPlugin",
        ]
    },
    install_requires=[
        "mkdocs>=1.0",
    ],
)
