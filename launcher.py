import sys
import aws_classes as aws


if __name__ == "__main__":

    if sys.argv[1].lower() == "destroy":
        print("Destroy features not yet implemented")
        raise NotImplementedError
    else:
        instance_factory = aws.InstanceFactory("config.ini")
        print(instance_factory)
        new_instance = instance_factory.launch_instance()
        print("Instance created")

        client = instance_factory.get_client()

        new_instance.self_destruct(client)
        print("Instance destroyed")
