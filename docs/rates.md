Rates
=====

Rates are of the form `X/u` where `X` is a number of requests and
`u` is a unit from this list:

- `s` - second
- `m` - minute
- `h` - hour
- `d` - day

(For example, you can read `5/s` as "five per second.")

!!! note

    Setting a rate of 0 per any unit of time will disallow requests, e.g.
    `0/s` will prevent any requests to the endpoint.


Rates may also be set to `None`, which indicates "there is no limit." Usage will not be tracked.

You may also specify a number of units, i.e.: `X/Yu` where `Y` is a number of units. If `u` is omitted, it is
presumed to be seconds. So, the following are equivalent, and all mean "one hundred requests per five
minutes":

- `100/5m`
- `100/300s`
- `100/300`

