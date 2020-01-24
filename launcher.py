import sys
import aws_classes as aws
import gui_elements as gui


if __name__ == "__main__":

    

    if sys.argv[1].lower() == "destroy":
        config_file = sys.argv[2]
        try:
            instance_factory = aws.InstanceFactory(config_file)
            instance_to_destroy = instance_factory.load_instance_from_savefile()
            client = instance_factory.get_client()
            instance_to_destroy.self_destruct(client)
            print("Instance destroyed")
        except Exception as e:
            print("Error during process. Check your AWS console manually.")
            print(f"Error details:\n{e}")
    else:
        try:
            config_file = sys.argv[1]
            instance_factory = aws.InstanceFactory(config_file)
            print(instance_factory)
            new_instance = instance_factory.launch_instance()
            print("Instance created")
        except Exception as e:
            print("Error during process. Check your AWS console manually.")
            print(f"Error details:\n{e}")