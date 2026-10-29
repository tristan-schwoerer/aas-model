"""The lab's resource types and the conventions they share.

- ``resources``: the AAS type hierarchy, from ``Resource`` to the concrete station and shuttle types, each with
  the submodels and capabilities that hold for its kind.
- ``operational``: the PackML contract every operational device speaks, per protocol (interfaces, control
  component, mappings, variables), and the command schemas.
- ``references``: references into a resource's own submodels and the idShorts of its interfaces.

The submodel templates these build on (IDTA templates and our extensions) are in ``aas_model.submodel_templates``.
"""

from .resources import (
    CappingStation, CompositeResource, DispensingStation, HandlingStation, InspectionStation, LoadingStation,
    MqttOperationalStation, MqttSoftwareResource, OpcuaOperationalStation, OperationalResource, PhysicalResource,
    PlanarShuttle, ProcessingStation, Resource, ResourceTypeAAS, Shuttle, SoftwareResource, Station,
    StopperingStation, TransportResource, UnloadingStation,
)
from .references import (
    MQTT_INTERFACE, OPCUA_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_ref,
    operation_variable_ref, series_segment_ref, skill_ref, variable_ref,
)

__all__ = [
    "Resource", "ResourceTypeAAS", "PhysicalResource", "OperationalResource",
    "Station", "MqttOperationalStation", "OpcuaOperationalStation", "ProcessingStation", "HandlingStation",
    "StopperingStation", "CappingStation", "DispensingStation", "LoadingStation", "UnloadingStation",
    "InspectionStation",
    "TransportResource", "Shuttle", "PlanarShuttle",
    "SoftwareResource", "MqttSoftwareResource",
    "CompositeResource",
    "MQTT_INTERFACE", "OPCUA_INTERFACE",
    "action_member_ref", "affordance_ref", "capability_ref", "operation_ref", "operation_variable_ref",
    "series_segment_ref", "skill_ref", "variable_ref",
]
