# Custom AWS Jupyter Launcher

Python script to launch an EC2 instance, with custom specs and software according to the callers parameters.
Includes a simple mechanism to record the details of what you launch, and they a single command teardown process.

### **Important:**

*The code here is free to use, but it requires that you have an AWS account and that you provide it with the access key and secret key associated with a user on your account. Any activity will be billed to the account associated with that account and user. Your keys are not visible or shared with any service except AWS.*

**Don't assume the teardown function is 100% perfect. Go back and check regularly that elastic IPs and running EC2 instances have been terminated. Both of these will incur ongoing costs**

### Steps to set-up
- [x] Download this repository with `git clone https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher.git`
- [x] [Create an AWS account](https://aws.amazon.com/resources/create-account/) 
- [x] Creating a user and credentials (*see below*)
- [x] Update the config.ini file with your user credentials

## Creating a user and credentials

The following images take you step by step through the process of creating a new user on your AWS account and giving them (only) the necessary permissions to create an EC2 instance.

**Go to the IAM service page:**
![select_iam_service](https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher/blob/master/imgs/select_iam.png)

**Then the IAM user management section:**
![goto_iams_user_section](https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher/blob/master/imgs/users.png)

**Create a new user:**
![create_new_user](https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher/blob/master/imgs/user_create.png)

**Give the user these permissions:**
![set_user_permissions](https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher/blob/master/imgs/permissions.png)

**Optionally, add a tag to remind you in the future why you created this user. It's also helpful to know in the future so you can delete a user, created solely for this purpose:**
![add_optional_tag](https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher/blob/master/imgs/tags.png)


**Finally, download the csv with the credentials for this user. You will not get any additional opportunity to download the secret key so make sure you download it:**
![download_cv](https://github.com/DanielJohnHarty/custom_aws_jupyter_launcher/blob/master/imgs/dl_cv.png)
