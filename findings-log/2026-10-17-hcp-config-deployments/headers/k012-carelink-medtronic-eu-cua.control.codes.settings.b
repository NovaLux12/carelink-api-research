{
  "predefined_control_codes_regexp": "(dpml:[0-3])|(tcc:[1-7])|(tup:((?i)TUP|LTU|DTU|BGM|GST|NOGSTU|NONE))|(lhpro:\\d+)|(lghpro:\\d+)|(vex:\\d+)|(ssd:(t|f))",
  "custom_control_codes_regexp": "(gstpro:\\d+)|(gstrc:(t|f))",
  "expiration_period_settings": {
    "DEFAULT": {
      "min": 1,
      "max": 30,
      "value": 3
    },
    "tcc": {
      "min": 1,
      "max": 30,
      "value": 1
    }
  },
  "ranges": {
    "dpml": {
      "min": 0,
      "max": 3
    },
    "tcc": {
      "min": 1,
      "max": 7
    },
    "lhpro": {
      "min": 0,
      "max": 4294967295
    },
    "lghpro": {
      "min": 0,
      "max": 4294967295
    },
    "vex": {
      "min": 0,
      "max": 100
    },
    "gstpro": {
      "min": 0,
      "max": 9223372036854775807
    }
  }
}