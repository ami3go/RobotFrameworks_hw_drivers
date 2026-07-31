# Normalized legacy command catalog

The legacy frame is 26 bytes: `AA`, address, command, 22 information bytes, checksum. Command semantics remain validation-gated where noted.

| Manual ID | Command code(s) | Description | Source line |
|---|---|---|---:|
| 12.1 | `20H` | 20H Set | 122 |
| 12.2 | `21H` | Set the input | 123 |
| 12.3 | `22H/23H` | Set/Read max input | 124 |
| 12.4 | `24H/25H` | Set/Read the max | 125 |
| 12.5 | `26H/27H` | Set/Read max input | 126 |
| 12.6 | `28H/29H` | Select/Read operation mode (CC/CV/CW/CR) of electronic load. (28H/29H) | 127 |
| 12.7 | `2AH/2BH` | Set/Read current | 128 |
| 12.8 | `2CH/2DH` | 8. Set/Read | 130 |
| 12.9 | `2EH/2FH` | 9. Set/Read | 131 |
| 12.10 | `30H/31H` | 10. Set/Read | 132 |
| 12.11 | `32H/33H` | Set/Read CC mode transient current and timer parameter. (32H/33H) | 133 |
| 12.12 | `34H/35H` | Set/Read CV transient voltage and timer parameter. (34H/35H) | 134 |
| 12.13 | `36H/37H` | Set/Read CW transient watt and timer paramete. (36H/37H) | 135 |
| 12.14 | `38H/39H` | Set/Read CR transient resistance and timer paramete. (38H/39H) | 136 |
| 12.15 | `3AH/3BH` | Set /Read | 137 |
| 12.16 | `3CH/3DH` | Set/Read the list | 139 |
| 12.17 | `3EH/3FH` | Set/Read list step | 140 |
| 12.18 | `40H/41H` | Set/Read one of the step’s current and time values. (40H/41H) | 141 |
| 12.19 | `4CH/4DH` | Save/Recall list | 142 |
| 12.20 | `50H/51H` | Setting/Reading timer | 144 |
| 12.21 | `52H/53H` | Disable/Enable timer of FOR LOAD ON (52H); Read timer state of FOR LOAD ON (53H) | 145 |
| 12.22 | `54H` | Set communication | 146 |
| 12.23 | `55H` | Enable/Disable LOCAL | 148 |
| 12.24 | `56H/57H` | Enable/Disable remote | 149 |
| 12.25 | `58H/59H` | Set/Read trigger | 150 |
| 12.26 | `5AH` | Send a trigger signal to trigging the electronic load. (5AH) | 151 |
| 12.27 | `5BH/5CH` | Saving/Recall user’s setting value in appointed memory area for recall. | 152 |
| 12.28 | `5DH/5EH` | Selecting/Reading FIXED/SHORT/TRAN/LIST/ BATTERY function mode. (5DH/5EH) | 153 |
| 12.29 | `5FH` | Read input voltage, current, power and relative state. (5FH) | 154 |
| 12.30 | `informational` | Operation status | 155 |
| 12.31 | `5FH response status` | Read status | 157 |
| 12.32 | `01H` | Read the information of E-Load (rated max current, max voltage, min voltage, max power, max | 158 |
| 12.33 | `02H/03H` | Set/Read hardware | 161 |
| 12.34 | `80H/81H` | Set/Read OCP | 162 |
| 12.35 | `82H/83H` | Set/Read OCP | 163 |
| 12.36 | `84H/85H` | Enable/Disable OCP function. | 164 |
| 12.37 | `86H/87H` | Set/Read | 167 |
| 12.38 | `88H/89H` | Set/Read | 169 |
| 12.39 | `8AH/8BH` | Set/Read | 170 |
| 12.40 | `8CH/8DH` | Set/Read | 171 |
| 12.41 | `8EH/8FH` | Set/Read | 172 |
| 12.42 | `90H` | Clear | 173 |
| 12.43 | `91H/92H` | Enable/Disable voltage autorange function. (91H/92H) | 174 |
| 12.44 | `93H/94H` | Enabel/Disable | 175 |
| 12.45 | `9DH` | Send | 177 |
| 12.46 | `A0H` | Read the information of load (on-load capacitance, on-load time…). (A0H) | 178 |
| 12.47 | `A1H` | Read the information of E-load (max/min input voltage/current). (A1H) | 179 |
| 12.48 | `A2H` | Read | 180 |
| 12.49 | `A3H` | Read | 182 |
| 12.50 | `A4H` | Read | 183 |
| 12.51 | `A5H` | Read | 184 |
| 12.52 | `A6H` | Read | 185 |
| 12.53 | `B0H/B1H` | Set/Read | 186 |
| 12.54 | `B2H/B3H` | Set/Read | 187 |
| 12.55 | `B4H/B5H` | Set/Read the voltage upper limit in CC mode. (B4H/B5H) | 188 |
| 12.56 | `B6H/B7H` | Set/Read the voltage lower limit in CC mode. (B6H/B7H) | 189 |
| 12.57 | `B8H/B9H` | Set/Read the current upper limit in CV mode. (B8H/B9H) | 190 |
| 12.58 | `BAH/BBH` | Set/Read the current lower limit in CV mode. (BAH/BBH) | 191 |
| 12.59 | `BCH/BDH` | Set/Read the voltage upper limit in CW mode. (BCH/BDH) | 192 |
| 12.60 | `BEH/BFH` | Set/Read the voltage lower limit in CW mode (BEH/BFH) | 193 |
| 12.61 | `C0H/C1H` | Set/Read max input resistance setting of E-load. (C0H/C1H) | 194 |
| 12.62 | `C2H/C3H` | Set/Read the voltage upper limit in CR mode. (C2H/C3H) | 195 |
| 12.63 | `C4H/C5H` | Set/Read the voltage lower limit in CR mode. (C4H/C5H) | 196 |
| 12.64 | `C6H/C7H` | Set/Read | 197 |
| 12.65 | `D0H/D1H` | Set/Read | 199 |
| 12.66 | `D2H/D3H` | Set/Read | 200 |
| 12.67 | `D4H/D5H` | Set/Read | 201 |
| 12.68 | `D6H/D7H` | Set/Read single-step on-load time of autotest mode. ( D6H/D7H) | 202 |
| 12.69 | `D8H/D9H` | Set/Read delay time of single-step in autotest mode. ( D8H/89H) | 203 |
| 12.70 | `DAH/DBH` | Set/Read single-step off-load time of autotest mode. (DAH/DBH) | 204 |
| 12.71 | `DCH/DDH` | Set/Read | 205 |
| 12.72 | `DEH/DFH` | Set/Read | 207 |
| 12.73 | `E0H/E1H` | Save/Recall | 208 |
| 12.74 | `0EH/0FH` | Set/Read | 209 |
| 12.75 | `10H/11H` | Set/Read | 210 |
