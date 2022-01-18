from dataclasses import dataclass

import sagemaker
from smallmatter.pathlib import Path2, S3Path

# @dataclass
# class DataPaths:
#     # bucket_name: S3Path = S3Path(sagemaker.Session().default_bucket())
#     # bucket_prefix: str = "textract-transformers"
#     #data_prefix: S3Path = bucket_name / bucket_prefix / "data"

#     imgs_s3uri: S3Path = data_prefix / "imgs-clean"
#     textract_s3uri: S3Path = data_prefix / "textracted"
#     annotations_base_s3uri: S3Path = data_prefix / "annotations"


@dataclass
class DataPaths:
    data_prefix: Path2 = Path2("data")
    imgs: Path2 = data_prefix / "imgs-clean"
    textracted: Path2 = data_prefix / "textracted"
    annotations: Path2 = data_prefix / "annotations"


@dataclass
class S3DataPaths(DataPaths):
    bucket_name: S3Path = S3Path(sagemaker.Session().default_bucket())
    bucket_prefix: str = "textract-transformers"
    data_prefix: Path2 = bucket_name / bucket_prefix / "data"
