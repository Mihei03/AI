import MainWindow
import bootstrapper
import json

if __name__ == "__main__":
    try:
        with open("config.json", 'r') as f:
            config_data = json.load(f)              
    except json.JSONDecodeError as e:
        config_data = {}
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
    except FileNotFoundError as e:
        config_data = {}
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
    
    if "initial_setup_done" not in config_data or config_data["initial_setup_done"] == "True":
        bootstrapper.initial_setup()
        config_data["first_load"] = "True"
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
    
    MainWindow.show()