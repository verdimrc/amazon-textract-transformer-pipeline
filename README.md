# Post-Process OCR Results with Transformer Models on Amazon SageMaker

[Amazon Textract](https://docs.aws.amazon.com/textract/latest/dg/what-is.html) is a service that automatically extracts text, handwriting, and some structured data from scanned documents: Going beyond simple optical character recognition (OCR) to identify and extract data from tables (with rows and cells), and forms (as key-value pairs).

In this "Amazon Textract Transformer Pipeline" sample and accompanying [blog post](https://aws.amazon.com/blogs/machine-learning/bring-structure-to-diverse-documents-with-amazon-textract-and-transformer-based-models-on-amazon-sagemaker/), we show how you can also automate more complex and domain-specific extraction tasks by integrating trainable models on [Amazon SageMaker](https://aws.amazon.com/sagemaker/).

We demonstrate **layout-aware entity extraction** on an example use case in finance, for which you could also consider using [Amazon Comprehend's native document analysis feature](https://aws.amazon.com/blogs/machine-learning/extract-custom-entities-from-documents-in-their-native-format-with-amazon-comprehend/).

However, this pipeline provides a framework you could further extend or customize for your own datasets and ML-based, OCR post-processing models.

## Background

To automate document understanding for business processes, we typically need to extract and standardize specific attributes from input documents: For example vendor and line item details from purchase orders; or specific clauses within contracts.

With Amazon Textract's [structure extraction utilities for forms and tables](https://aws.amazon.com/textract/features/), many of these requirements are trivial out of the box with no custom training required. For example: "pull out the text of the third column, second row of the first table on page 1", or "find what the customer wrote in for the `Email address:` section of the form".

We can also use standard text processing models or AI services like [Amazon Comprehend](https://aws.amazon.com/comprehend/) to analyze extracted text. For example: picking out `date` entities on a purchase order that may not be explicitly "labelled" in the text - perhaps because sometimes the date just appears by itself in the page header. However, many standard approaches treat text as a flat 1D sequence of words.

Since Textract also outputs the *positions* of each detected 'block' of text, we can even write advanced templating rules in our solution code. For example: "Find text matching XX/XX/XXXX within the top 5% of the page height".

But what about use cases needing still more intelligence? Where, even with these tools, writing rule-based logic to extract the specific information you need is too challenging?

For some use cases, incoming documents are highly variable so simple position-based templating methods may not work well... And the content of the text needs to be accounted for as well. For example:

- In analysing traditional [letters](https://en.wikipedia.org/wiki/Letter_(message)), extracting sender and recipient **addresses** may be difficult for pure text-processing models (because location cues are important), but also hard via templating (because different letterheads or formatting choices may significantly offset the address locations).
- In commercial business documents, the **name of the vendor** may often be present in front-matter or headers, but usually not specifically labelled e.g. as `Vendor:` - which might help Textract's Key-Value feature extract it.
- For detecting **subheadings within documents**, it may be possible to write general rules based on text size and relative position - but these could grow very complex if considering, for example, documents with multiple columns or high variability in text size.

In all these cases and others like them, it may be useful to apply an ML model that **jointly** considers the text itself, and its position on the page.


## Solution Overview

This sample sets up a **pipeline** orchestrated by [AWS Step Functions](https://aws.amazon.com/step-functions/), as shown below:

![](img/architecture-overview.png "Architecture overview diagram")

Documents uploaded to the input bucket automatically trigger the workflow, which:

1. Extracts document data using Amazon Textract.
2. Enriches the Textract response JSON with extra insights using an ML model deployed in SageMaker.
3. Consolidates the business-level fields in a post-processing Lambda function.
4. (If any expected fields were missing or low-confidence), forwards the results to a human reviewer.

In the provided example, input documents are specimen **credit card agreements** per **[this dataset](https://www.consumerfinance.gov/credit-cards/agreements/)** published by the [US Consumer Finance Protection Bureau (CFPB)](https://www.consumerfinance.gov/).

We define a diverse set of "fields" of interest: from short entity-like fields (such as provider name, credit card name, and effective date), to longer and more flexible concepts (like "minimum payment calculation method" and "terms applicable to local areas only").

Bounding box ananotations are collected to train a SageMaker ML model to classify the words detected by Amazon Textract between these field types - using **both** the content of the text and the location/size of each word as inputs:

![](img/annotation-example-trimmed.png "screenshot of annotated page")

From this enriched JSON, the post-processing Lambda can apply simple rule-based logic to extract and validate the fields of interest.

For any documents where required fields could not be detected confidently, the output is forwarded to human review using [Amazon Augmented AI (A2I)](https://aws.amazon.com/augmented-ai/) with a customized **task template** UI:

![](img/human-review-sample.png "screenshot of human review UI")

By orchestrating the process through AWS Step Functions (rather than point-to-point integrations between each stage for example), we gain the benefits that the overall flow can be graphically visualized and individual stages can be more easily customized. A wide range of integration options are available for adding new stages and storing results (or triggering further workflows) from the output:

![](img/sfn-execution-screenshot.png "screenshot of workflow graph in AWS Step Functions console")


## Getting Started

To build and deploy this solution, you'll first need to install:

- The [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install) (which depends on [NodeJS](https://nodejs.org/en/)).
- [Python v3.6+](https://www.python.org/)
- (Optional but recommended) consider using [Poetry](https://python-poetry.org/docs/#installation) rather than Python's built-in `pip`.

You'll also need to [bootstrap your CDK environment](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html#bootstrapping-howto) **with the modern template** (i.e. setting `CDK_NEW_BOOTSTRAP=1`, as described in the docs).

> 🚀 **To try the solution out with your own documents and entity types:** Review the standard steps below first, but find further guidance in [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md).

**Step 1: Set up and activate the project's virtual environment**

If you're using Poetry, you should be able to simply run (from this folder):

```sh
poetry shell
```

Otherwise, you can instead run:

```sh
# (Create the virtual environment)
python3 -m venv .venv
# (Activate the virtual environment)
source .venv/bin/activate
```

Depending on your setup, your Python v3 installation may simply be called `python` instead of `python3`. If you're on Windows, you can instead try to activate by running `.venv\Scripts\activate.bat`.

**Step 2: Install project dependencies**

Once the virtual environment is active, install the required dependencies by running:

```sh
# For Poetry:
poetry install
# ...OR, without Poetry:
pip install -e .[dev]
```

**Step 3: Deploy the solution stacks with CDK**

To deploy (or update, if already deployed) all stacks in the solution to your default AWS Region, run:

```sh
cdk deploy --all
# To skip approval prompts, you can optionally add: --require-approval never
```

> Note that some AWS Regions may not support all services required to run the solution, but it has been tested successfully in at least `ap-southeast-1` (Singapore) and `us-east-2` (Ohio).

You'll be able to see the deployed stacks in the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/home?#/stacks).

**Step 4: Set up your notebook environment in Amazon SageMaker**

The solution stack does not automatically spin up a SageMaker notebook environment because A) there are multiple options and B) users may have an existing one already.

If you're able, we recommend following the instructions to [onboard to SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-onboard.html) for a more fully-featured user experience and easier setup.

If this is not possible, you can instead choose to [create a classic SageMaker Notebook Instance](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-console.html). If using a classic notebook instance:

- Instance type `ml.t3.medium` and volume size `30GB` should be sufficient to run through the sample
- This repository uses interactive notebook widgets, so you'll need to install extension `@jupyter-widgets/jupyterlab-manager` either through the extensions manager UI (*Settings > Enable Extension Manager*) or by attaching a [lifecycle configuration script](https://docs.aws.amazon.com/sagemaker/latest/dg/notebook-lifecycle-config.html) customizing the [install-lab-extension template](https://github.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples/tree/master/scripts/install-lab-extension) to to reference this particular extension.

Whichever environment type you use, the **execution role** attached to your Notebook Instance or Studio User Profile will need some additional permissions beyond basic SageMaker access:
  - Find your deployed OCR pipeline stack in the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/home?#/stacks) and look up the `DataSciencePolicyName` from the **Outputs** tab.
  - Next, find your studio user's or notebook instance's *SageMaker execution role* in the [AWS IAM Roles Console](https://console.aws.amazon.com/iamv2/home#/roles)
  - Click the **Attach policies** button to attach the stack's created data science policy to your SageMaker role.

> ⚠️ **Warning:** The managed `AmazonSageMakerFullAccess` policy that some SageMaker on-boarding guides suggest to use grants a broad set of permissions. This can be useful for initial experimentation, but you should consider scoping down access further for shared or production environments.
>
> *In addition* to the `DataSciencePolicy` created by the stack, this sample assumes that your SageMaker execution role has permissions to:
>
> - Access the internet (to install some additional packages)
> - Read and write the SageMaker default S3 bucket
> - Train, and deploy models (and optionally perform automatic hyperparameter tuning) on GPU-accelerated instance types - and invoke the deployed endpoint to test the model
> - Create SageMaker Ground Truth labeling jobs
> - Create task templates and workflow definitions in Amazon A2I
>
> To learn more about security with SageMaker, and get started implementing additional controls on your environment, you can refer to the [Security section of the SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/security.html) - as well as this [AWS ML Blog Post](https://aws.amazon.com/blogs/machine-learning/building-secure-machine-learning-environments-with-amazon-sagemaker/) and associated [workshops](https://sagemaker-workshop.com/security_for_sysops.html).

Once your environment is set up, you can:

- Open JupyterLab (clicking 'Open Studio' for Studio, or 'Open JupyterLab' for a NBI)
- Open a system terminal window in JupyterLab
- (If you're on a new SageMaker Notebook Instance, move to the Jupyter root folder with `cd ~/SageMaker`)
- Clone in this repository with:

```sh
git clone https://github.com/aws-samples/amazon-textract-transformer-pipeline
```

**Step 5: Follow through the setup notebooks**

The Python notebooks in the [notebooks/ folder](notebooks) will guide you through the remaining activities to annotate data, train the post-processing model, and configure and test the solution stack. Open each of the `.ipynb` files in numbered order to follow along.


## Next Steps

For this demo we selected the credit card agreement corpus as a good example of a challenging dataset with lots of variability between documents, and realistic commercial document formatting and tone (as opposed to, for example, academic papers).

We also demonstrated detection of field/entity types with quite different characteristics: From short values like annual fee amounts or dates, to full sentences/paragraphs.

The approach should work well for many different document types, and the solution is designed with customization of the field list in mind.

However, there are many more opportunities to extend the approach. For example:

- Rather than token/word classification, alternative '**sequence-to-sequence**' ML tasks such as could be applied: Perhaps to fix common OCR error patterns, or to build general question-answering models on documents.
- Just as the BERT-based model was extended to consider coordinates as input, perhaps **source OCR confidence scores** (also available from Textract) would be useful model inputs.
- The post-processing Lambda function could be extended to perform more complex validations on detected fields: For example to extract numerics, enforce regular expression matching, or even call some additional AI service such as Amazon Comprehend.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file. Included annotation datasets are licensed under the Creative Commons Attribution 4.0 International License. See the [notebooks/data/annotations/LICENSE](notebooks/data/annotations/LICENSE) file.
