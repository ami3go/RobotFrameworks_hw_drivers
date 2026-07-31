# Normalized SCPI command catalog

Generated from the supplied manual table of contents. Query forms implied by the manual are represented by the same command-family row.

| Manual ID | Command family | Source line |
|---|---|---:|
| 1.1 | `*CLS` | 3 |
| 1.2 | `*ESE` | 4 |
| 1.3 | `*ESR?` | 5 |
| 1.4 | `*IDN?` | 6 |
| 1.5 | `*OPC` | 7 |
| 1.6 | `*PSC` | 8 |
| 1.7 | `*RCL` | 9 |
| 1.8 | `*RST` | 10 |
| 1.9 | `*SAV` | 11 |
| 1.10 | `*SRE` | 12 |
| 1.11 | `*STB?` | 13 |
| 1.12 | `*TST?` | 14 |
| 3.1 | `SSTATus:QUEStionable[:EVENt]?` | 21 |
| 3.2 | `STATus:QUEStionable:CONDition?` | 22 |
| 3.3 | `STATus:QUEStionable:ENABle` | 23 |
| 3.4 | `STATus:OPERation[:EVENt]?` | 24 |
| 3.5 | `STATus:OPERation:CONDition?` | 25 |
| 3.6 | `STATus:OPERation:ENABle` | 26 |
| 4.1 | `MEASure[:SCALar]:VOLTage[:DC]?` | 28 |
| 4.2 | `MEASure[:SCALar]:VOLTage:MAXimum?` | 29 |
| 4.3 | `MEASure[:SCALar]:VOLTage:MINimum?` | 30 |
| 4.4 | `MEASure[:SCALar]:VOLTage:PTPeak?` | 31 |
| 4.5 | `MEASure[:SCALar]:CURRent[:DC]?` | 32 |
| 4.6 | `MEASure[:SCALar]:CURRent:MAXimum?` | 33 |
| 4.7 | `MEASure[:SCALar]:CURRent:MINimum?` | 34 |
| 4.8 | `MEASure[:SCALar]:CURRent:PTPeak?` | 35 |
| 4.9 | `MEASure[:SCALar]:POWer[:DC]?` | 36 |
| 4.10 | `MEAS[:SCALar]:RESistance[:DC]?` | 37 |
| 5.1 | `LED:VOLTage` | 39 |
| 5.2 | `LED:CURRent` | 40 |
| 5.3 | `LED:RCOeff` | 41 |
| 5.5 | `OCP[:STATe]` | 43 |
| 5.6 | `OCP:ISTart` | 44 |
| 5.7 | `OCP:IEND` | 45 |
| 5.8 | `OCP:STEP` | 46 |
| 5.9 | `OCP:DWELl` | 47 |
| 5.10 | `OCP:VTRig` | 48 |
| 5.11 | `OCP:RESult[:OCP]?` | 49 |
| 5.12 | `OCP:RESult:PMAX?` | 50 |
| 6.1 | `PEAK[:STATe]` | 55 |
| 6.2 | `PEAK CLEar` | 56 |
| 6.3 | `PEAK:VOLTage:MAXimum?` | 57 |
| 6.4 | `PEAK:VOLTage:MINimum?` | 58 |
| 6.5 | `PEAK:CURRent:MAXimum?` | 59 |
| 6.6 | `PEAK:CURRent:MINimum?` | 60 |
| 7.1 | `[SOURce:]INPut` | 62 |
| 7.2 | `[SOURce:]INPut:SHORt` | 63 |
| 7.3 | `[SOURce:]FUNCtion` | 64 |
| 7.4 | `[SOURce:]VOLTage:RANGe` | 65 |
| 7.5 | `[SOURce:]VOLTage:RANGe:AUTO[:STATe]` | 66 |
| 7.6 | `[SOURce:]VOLTage:[LEVel:]ON` | 67 |
| 7.7 | `[SOURce:]Voltage:[LEVel:]OFF` | 68 |
| 7.8 | `[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] <NRf+>` | 69 |
| 7.9 | `[SOURce:]CURRent:RANGe` | 70 |
| 7.10 | `[SOURce:]CURRent:SLEW[:BOTH]` | 72 |
| 7.11 | `[SOURce:]CURRent:SLEW:RISE` | 73 |
| 7.12 | `[SOURce:]CURRent:SLEW:FALL` | 74 |
| 7.13 | `[SOURce:]CURRent:PROTection[:LEVel]` | 75 |
| 7.14 | `[SOURce:]CURRent[:LEVel][:IMMediate][:AMPLitude] <NRf+>` | 76 |
| 7.15 | `[SOURce:]POWer:PROTection[:LEVel]` | 77 |
| 7.16 | `[SOURce:]POWer[:LEVel][:IMMediate][:AMPLitude] <NRf+>` | 79 |
| 7.17 | `[SOURce:]RESistance[:LEVel][:IMMediate][:AMPLitude] <NRf+>` | 80 |
| 7.18 | `[SOURce:]RESistance[:LEVel][:IMMediate][:AMPLitude]?` | 81 |
| 7.19 | `[SOURce:]DYNamic:HIGH[:LEVel]` | 83 |
| 7.20 | `[SOURce:]DYNamic:HIGH:DWELl` | 84 |
| 7.21 | `[SOURce:]DYNamic:LOW[:LEVel]` | 85 |
| 7.22 | `[SOURce:]DYNamic:LOW:DWELl` | 86 |
| 7.23 | `[SOURce:]DYNamic:SLEW` | 87 |
| 7.24 | `[SOURce:]DYNamic:SLEW:RISE` | 88 |
| 7.25 | `[SOURce:]DYNamic:SLEW:FALL` | 89 |
| 7.26 | `[SOURce:]DYNamic:MODE` | 90 |
| 8.1 | `SYSTem:ERRor?` | 92 |
| 8.2 | `SYSTem:VERSion?` | 93 |
| 8.3 | `SYSTem:SENSe[:STATe]` | 94 |
| 8.4 | `SYSTem:LOCal` | 95 |
| 8.5 | `SYSTem:REMote` | 96 |
| 8.6 | `SYSTem:RWLock` | 97 |
| 9.1 | `TIME:VOLTage:LOW` | 99 |
| 9.2 | `TIME:VOLTage:HIGH` | 100 |
| 9.3 | `TIME:VOLTage:UP?` | 101 |
| 9.4 | `TIME:VOLTage:DOWN?` | 102 |
| 10.1 | `TIMing[:STATe]` | 107 |
| 10.2 | `TIMing:LOAD:SETTing` | 108 |
| 10.3 | `TIMing:LOAD:MODE` | 109 |
| 10.4 | `TIM:LOAD:SETT OFF` | 110 |
| 10.5 | `TIMing:LOAD:VALue` | 111 |
| 10.6 | `TIMing:TSTart:SOURce` | 112 |
| 10.7 | `TIMing:TSTart:EDGE` | 113 |
| 10.8 | `TIMing:TSTart:LEVel` | 114 |
| 10.9 | `TIMing:TEND:SOURce` | 115 |
| 10.10 | `TIMing:TEND:EDGE` | 116 |
| 10.11 | `TIMing:TEND:LEVel` | 117 |
| 10.12 | `TIMing:RESult` | 118 |
