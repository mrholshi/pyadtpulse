# pyadtpulse

Interfaces with ADT Pulse home security portal.


## Usage

Set environment variable **ADT_PULSE_USERNAME** and **ADT_PULSE_PASSWORD**


```python
>>> from adtpulse import adtpulse
>>> ps = adtpulse.Adtpulse()
>>> ps.arm("stay")
>>> ps.disarm()
```