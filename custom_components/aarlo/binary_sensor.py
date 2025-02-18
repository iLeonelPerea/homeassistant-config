"""
This component provides HA sensor for Netgear Arlo IP cameras.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.arlo/
"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (BinarySensorEntity)
from homeassistant.const import (ATTR_ATTRIBUTION,
                                 CONF_MONITORED_CONDITIONS)
from homeassistant.core import callback
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from . import COMPONENT_ATTRIBUTION, COMPONENT_DATA, COMPONENT_BRAND, COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

# sensor_type [ description, class, attribute ]
SENSOR_TYPES = {
    'sound': ['Sound', 'sound', 'audioDetected'],
    'motion': ['Motion', 'motion', 'motionDetected'],
    'ding': ['Ding', 'occupancy', 'buttonPressed'],
    'cry': ['Cry', 'sound', 'babyCryDetection'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):
    """Set up an Arlo IP sensor."""
    arlo = hass.data.get(COMPONENT_DATA)
    if not arlo:
        return

    sensors = []
    for sensor_type in config.get(CONF_MONITORED_CONDITIONS):
        for camera in arlo.cameras:
            if camera.has_capability(SENSOR_TYPES.get(sensor_type)[2]):
                sensors.append(ArloBinarySensor(camera, sensor_type))
        for doorbell in arlo.doorbells:
            if doorbell.has_capability(SENSOR_TYPES.get(sensor_type)[2]):
                sensors.append(ArloBinarySensor(doorbell, sensor_type))
        for light in arlo.lights:
            if light.has_capability(SENSOR_TYPES.get(sensor_type)[2]):
                sensors.append(ArloBinarySensor(light, sensor_type))

    async_add_entities(sensors, True)


class ArloBinarySensor(BinarySensorEntity):
    """An implementation of a Netgear Arlo IP sensor."""

    def __init__(self, device, sensor_type):
        """Initialize an Arlo sensor."""
        self._name = '{0} {1}'.format(SENSOR_TYPES[sensor_type][0], device.name)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._device = device
        self._sensor_type = sensor_type
        self._state = None
        self._class = SENSOR_TYPES.get(self._sensor_type)[1]
        self._attr = SENSOR_TYPES.get(self._sensor_type)[2]
        _LOGGER.info('ArloBinarySensor: %s created', self._name)

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        def update_state(_device, attr, value):
            _LOGGER.debug('callback:' + self._name + ':' + attr + ':' + str(value)[:80])
            self._state = value
            self.async_schedule_update_ha_state()

        if self._attr is not None:
            self._state = self._device.attribute(self._attr)
            self._device.add_attr_callback(self._attr, update_state)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._class

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = {}

        attrs[ATTR_ATTRIBUTION] = COMPONENT_ATTRIBUTION
        attrs['brand'] = COMPONENT_BRAND
        attrs['friendly_name'] = self._name
        attrs['camera_name'] = self._device.name

        return attrs

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state is True
