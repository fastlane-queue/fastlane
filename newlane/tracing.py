import socket

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)

exporter = OTLPSpanExporter()
processor = BatchSpanProcessor(exporter)

resource = Resource.create({
    'service.name': 'fastlane',
    'service.instance.id': socket.gethostname()
})

provider = TracerProvider(resource=resource)
provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
