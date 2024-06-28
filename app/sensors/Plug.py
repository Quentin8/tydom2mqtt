import json
import logging
from .Sensor import Sensor

logger = logging.getLogger(__name__)

switch_config_topic = "homeassistant/switch/tydom/{id}/config"


switch_state_topic = "switch/tydom/{id}/state" # Topic to read the current state

# The MQTT topic subscribed to receive a JSON dictionary payload and then set as sensor attributes
switch_attributes_topic = "switch/tydom/{id}/attributes" 

# WHere to publish commands
switch_command_topic = "switch/tydom/{id}/set" # Topic to publish commands

typeFromClassName = {
    "Plug": "outlet"
}

class Plug:
    def __init__(self, tydom_attributes, mqtt=None):
        self.config = None
        self.device = None
        
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.name = self.attributes['switch_name']
        self.state = tydom_attributes['state']
        
        self.config_topic =  switch_config_topic.format(id=self.id)
        self.command_topic = switch_command_topic.format(id=self.id)
        self.json_attributes_topic = switch_attributes_topic.format(id=self.id)
        self.state_topic = switch_state_topic.format(id=self.id)
        
        self.mqtt = mqtt

    async def setup(self):
        self.device = {
            'manufacturer': 'Delta Dore',
            'model': f'{self.__class__.__name__}',
            'name': self.name,
            'identifiers': self.id}
        
        
        self.config = {
            'name': None,  # set an MQTT entity's name to None to mark it as the main feature of a device
            'unique_id': self.id,
            'command_topic': self.command_topic,
            'state_topic': self.state_topic,
            'json_attributes_topic': self.json_attributes_topic,
            'payload_on': "ON",
            'payload_off': "OFF",
            'retain': 'false',
            'device_class': typeFromClassName.get(f"{self.__class__.__name__}"),
            'device': self.device
        }

        # Create the device
        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(
                self.config_topic, json.dumps(
                    self.config), qos=0, retain=True)
            
    async def update(self):
        await self.setup()

        # See if it's possible to keep it here or in MessageHandler ?
        # try:
        #     await self.update_sensors()
        # except Exception as e:
        #     logger.error("Switch sensors Error :")
        #     logger.error(e)


        if self.mqtt is not None:
            # Sends current switch state
            self.mqtt.mqtt_client.publish(
                self.state_topic,
                self.state,
                qos=0,
                retain=True)
            
            # Sets sensors attributes with self.attributes dict
            self.mqtt.mqtt_client.publish(
                self.config['json_attributes_topic'],
                self.attributes,
                qos=0,
                retain=True)
            
        logger.info(
            "Switch created / updated : %s %s %s",
            self.name,
            self.id,
            self.state)


    @staticmethod
    async def set_state(tydom_client, device_id, switch_id, state):
        logger.info("%s %s %s", switch_id, 'state', state)
        if not (state == ''):
            await tydom_client.put_devices_data(device_id, switch_id, 'plugCmd', state)