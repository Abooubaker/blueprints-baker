"""Programming Agent — pin-mapped, multi-language starter bundles.

The generated code is deliberately a scaffold: it uses the real controller pin
map from the electrical plan, but every control loop still needs the builder to
verify it on hardware. Python, Arduino C++, and STM32 C get the most structure;
the remaining selected languages get compilable skeletons with explicit TODOs.
"""

from __future__ import annotations

from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentRequest,
    CodeFile,
    ElectricalPlan,
    LanguageBundle,
    ProgrammingInput,
    ProgrammingOutput,
)
from app.models.enums import AgentName, CodeLanguage

_DISPLAY = {
    CodeLanguage.PYTHON: "Python",
    CodeLanguage.CPP: "C++ (Arduino)",
    CodeLanguage.C: "C (STM32 HAL)",
    CodeLanguage.STM32_ASSEMBLY: "STM32 assembly",
    CodeLanguage.VERILOG: "Verilog",
    CodeLanguage.VHDL: "VHDL",
    CodeLanguage.OTHER: "Other language",
}

_FRAMEWORK = {
    CodeLanguage.PYTHON: "MicroPython",
    CodeLanguage.CPP: "Arduino / PlatformIO",
    CodeLanguage.C: "STM32 HAL",
    CodeLanguage.STM32_ASSEMBLY: "ARM Cortex-M",
    CodeLanguage.VERILOG: "RTL",
    CodeLanguage.VHDL: "RTL",
    CodeLanguage.OTHER: "",
}

_STATUS: dict[CodeLanguage, str] = {
    CodeLanguage.PYTHON: "scaffold",
    CodeLanguage.CPP: "scaffold",
    CodeLanguage.C: "scaffold",
    CodeLanguage.STM32_ASSEMBLY: "scaffold",
    CodeLanguage.VERILOG: "scaffold",
    CodeLanguage.VHDL: "scaffold",
    CodeLanguage.OTHER: "scaffold",
}


def _sanitize(value: str) -> str:
    cleaned = "".join(character if character.isalnum() else "_" for character in value.upper())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "PIN"


def _pin_map(plan: ElectricalPlan) -> dict[str, str]:
    """Signal/net name -> controller pin, derived from the electrical pinout."""

    controller = next((node for node in plan.nodes if node.kind == "controller"), None)
    if controller is None:
        return {}
    aliases: dict[str, str] = {}
    used: set[str] = set()
    for entry in plan.pinout:
        if entry.ref != controller.ref or not entry.connected:
            continue
        label = entry.signal or entry.net or entry.pin
        alias = _sanitize(label)
        if alias in used and aliases.get(alias) != entry.pin:
            alias = f"{alias}_{_sanitize(entry.pin)}"
        aliases[alias] = entry.pin
        used.add(alias)
    return dict(sorted(aliases.items()))


def _parsed_languages(raw: object) -> list[CodeLanguage]:
    if not isinstance(raw, list) or not raw:
        return [CodeLanguage.PYTHON, CodeLanguage.CPP]
    languages: list[CodeLanguage] = []
    for value in raw:
        try:
            language = CodeLanguage(str(value))
        except ValueError:
            continue
        if language not in languages:
            languages.append(language)
    return languages or [CodeLanguage.PYTHON, CodeLanguage.CPP]


def _python_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    constants = "\n".join(f'{name} = "{pin}"' for name, pin in pins.items()) or "# No pins mapped."
    robot = f'''"""Robot behaviour for {robot_name}."""

from config import LOOP_HZ, SERIAL_BAUD, PINS
import time


class Robot:
    """Starter control loop generated from the Albayraq pin map."""

    def __init__(self) -> None:
        self.running = False

    def setup(self) -> None:
        print("Booting {robot_name}")
        # TODO: initialise motors, sensors, and safe output states for your board.
        self.running = True

    def step(self) -> None:
        """Run one control iteration."""
        # TODO: read sensors, compute an error, and command the motors.
        # Pin names are available through ``PINS`` in config.py.
        time.sleep(1 / LOOP_HZ)

    def stop(self) -> None:
        self.running = False
        # TODO: drive every motor output to a safe low state.
        print("Stopped")


def make_robot() -> Robot:
    return Robot()
'''
    main = '''"""Entry point. Copy this project to the board, then run main.py."""

from robot import make_robot


def main() -> None:
    robot = make_robot()
    robot.setup()
    try:
        while robot.running:
            robot.step()
    except KeyboardInterrupt:
        pass
    finally:
        robot.stop()


if __name__ == "__main__":
    main()
'''
    config = f'''"""Pin map generated from the electrical plan. Do not edit by hand."""

SERIAL_BAUD = 115200
LOOP_HZ = 50

PINS = {{
{constants}
}}
'''
    readme = f"""# {robot_name} — MicroPython starter

1. Flash MicroPython to the controller.
2. Copy `config.py`, `robot.py`, and `main.py` to the board.
3. Open a serial console at 115200 baud and run `main.py`.
4. Fill in the TODO blocks in `robot.py` before connecting motors.

This is a scaffold generated from the validated pin map; verify every pin on
your own board before applying power.
"""
    return [
        CodeFile(path="config.py", language="python", content=config, explanation="Pin constants."),
        CodeFile(
            path="robot.py",
            language="python",
            content=robot,
            explanation="Control-loop skeleton with setup, step, and stop hooks.",
        ),
        CodeFile(path="main.py", language="python", content=main, explanation="Entry point."),
        CodeFile(path="README.md", language="markdown", content=readme, explanation="Run steps."),
    ]


def _cpp_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    constants = "\n".join(
        f"constexpr uint8_t PIN_{name} = {pin if pin.isdigit() else '0'};  // {pin}"
        for name, pin in pins.items()
    )
    if not constants:
        constants = "// No controller pins mapped."
    header = f"""#pragma once

#include <Arduino.h>

// Generated pin map. Non-numeric controller pins are kept in the comment and
// must be mapped to the board variant before compiling.
{constants}
"""
    main = f"""#include <Arduino.h>
#include "config.h"

// {robot_name} — pin-mapped starter firmware.

void setup() {{
  Serial.begin(115200);
  delay(200);
  Serial.println("{robot_name} booting");
  // TODO: configure each PIN_* with pinMode() for your board.
}}

void loop() {{
  // TODO: read sensors, compute an error, and command the motor driver.
  // Keep a watchdog and a safe stop path before running motors at speed.
  delay(20);
}}
"""
    platformio = f"""[env:albayraq]
platform = atmelavr
board = uno
framework = arduino
monitor_speed = 115200
build_flags = -DROBOT_NAME=\\"{robot_name}\\"
"""
    readme = f"""# {robot_name} — Arduino C++ starter

1. Install PlatformIO (or the Arduino IDE).
2. Check `include/config.h` against your controller variant.
3. Build and upload with `pio run -t upload`.
4. Fill in the TODO blocks in `src/main.cpp` before powering motors.

This is a pin-mapped scaffold, not verified firmware.
"""
    return [
        CodeFile(
            path="platformio.ini",
            language="ini",
            content=platformio,
            explanation="PlatformIO project configuration.",
        ),
        CodeFile(
            path="include/config.h",
            language="cpp",
            content=header,
            explanation="Generated pin constants.",
        ),
        CodeFile(
            path="src/main.cpp",
            language="cpp",
            content=main,
            explanation="Arduino setup/loop skeleton.",
        ),
        CodeFile(
            path="README.md", language="markdown", content=readme, explanation="Upload steps."
        ),
    ]


def _c_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    defines = "\n".join(f'#define PIN_{name} "{pin}"' for name, pin in pins.items())
    header = f"""#ifndef ROBOT_CONFIG_H
#define ROBOT_CONFIG_H

// Pin names are strings because STM32 port/pin assignment depends on the board.
{defines or "/* No pins mapped. */"}

#endif
"""
    main = f"""#include "main.h"
#include "config.h"

// {robot_name} — STM32 HAL starter.

void SystemClock_Config(void);
static void MX_GPIO_Init(void);

int main(void) {{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();

  while (1) {{
    // TODO: read sensors and command the motor driver through HAL_GPIO_WritePin.
    HAL_Delay(20);
  }}
}}

static void MX_GPIO_Init(void) {{
  // TODO: enable the GPIO clocks and configure every mapped pin.
  __HAL_RCC_GPIOA_CLK_ENABLE();
}}
"""
    readme = f"""# {robot_name} — STM32 C starter

1. Create an STM32CubeIDE project for your exact MCU.
2. Copy `Core/Inc/config.h` and `Core/Src/main.c` into it.
3. Implement `SystemClock_Config()` and the GPIO initialisation TODO.
4. Build, flash, and verify every pin with a meter before connecting loads.

The pin map is generated from the electrical plan; the HAL calls are a
scaffold and must match your board package.
"""
    return [
        CodeFile(
            path="Core/Inc/config.h",
            language="c",
            content=header,
            explanation="Generated pin constants.",
        ),
        CodeFile(
            path="Core/Src/main.c",
            language="c",
            content=main,
            explanation="HAL main loop skeleton.",
        ),
        CodeFile(path="README.md", language="markdown", content=readme, explanation="Board steps."),
    ]


def _assembly_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    text = "\n".join(f"; {name} -> {pin}" for name, pin in pins.items())
    startup = f"""; {robot_name} — minimal Cortex-M vector table scaffold.
.syntax unified
.cpu cortex-m4
.thumb

.section .isr_vector,"a",%progbits
.word 0x20001000
.word Reset_Handler

.section .text.Reset_Handler
.weak Reset_Handler
.thumb_func
Reset_Handler:
    ; TODO: copy .data, zero .bss, then call main.
    b main
"""
    main = f"""; {robot_name} — application scaffold.
; Generated pin notes:
{text or "; No pins mapped."}

.syntax unified
.thumb

.global main
.thumb_func
main:
    ; TODO: configure GPIO and run the control loop.
loop:
    b loop
"""
    readme = f"""# {robot_name} — STM32 assembly starter

1. Add `startup.s` and `main.s` to your STM32 project.
2. Match the vector table and stack pointer to your exact MCU.
3. Implement GPIO setup and the control loop.
4. Flash and verify with a debugger before enabling power outputs.

Assembly is provided as a scaffold. It is not a complete firmware image.
"""
    return [
        CodeFile(
            path="src/startup.s", language="assembly", content=startup, explanation="Vector table."
        ),
        CodeFile(path="src/main.s", language="assembly", content=main, explanation="Main loop."),
        CodeFile(path="README.md", language="markdown", content=readme, explanation="Build notes."),
    ]


def _verilog_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    ports = ",\n".join(f"    output wire {name.lower()}" for name in (pins or {"STATUS": "none"}))
    top = f"""// {robot_name} — RTL scaffold.
module top (
    input  wire clk,
    input  wire rst_n,
{ports}
);

    // TODO: implement the control law and drive each output.
    assign {next(iter(pins or {"STATUS": "none"})).lower()} = 1'b0;

endmodule
"""
    testbench = """`timescale 1ns/1ps
module top_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;
    initial begin
        #20 rst_n = 1;
        #200 $finish;
    end
    // TODO: instantiate top and add assertions.
endmodule
"""
    readme = f"""# {robot_name} — Verilog scaffold

1. Add `rtl/top.v` to your FPGA project and map the ports to real pins.
2. Implement the control law behind the TODO.
3. Simulate `tb/top_tb.v`, then synthesise for your target board.

This RTL is a scaffold; it does not implement a complete robotics controller.
"""
    return [
        CodeFile(path="rtl/top.v", language="verilog", content=top, explanation="Top module."),
        CodeFile(
            path="tb/top_tb.v", language="verilog", content=testbench, explanation="Testbench."
        ),
        CodeFile(path="README.md", language="markdown", content=readme, explanation="FPGA steps."),
    ]


def _vhdl_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    names = list((pins or {"STATUS": "none"}).keys())
    ports = ";\n".join(f"    {name.lower()} : out std_logic" for name in names)
    top = f"""-- {robot_name} — VHDL scaffold.
library ieee;
use ieee.std_logic_1164.all;

entity top is
  port (
    clk   : in  std_logic;
    rst_n : in  std_logic;
{ports}
  );
end entity top;

architecture rtl of top is
begin
  -- TODO: implement the control law and drive each output.
  {names[0].lower()} <= '0';
end architecture rtl;
"""
    testbench = """library ieee;
use ieee.std_logic_1164.all;

entity top_tb is
end entity top_tb;

architecture sim of top_tb is
  signal clk   : std_logic := '0';
  signal rst_n : std_logic := '0';
begin
  clk <= not clk after 5 ns;
  process
  begin
    wait for 20 ns;
    rst_n <= '1';
    wait for 200 ns;
    std.env.stop;
  end process;
  -- TODO: instantiate top and add assertions.
end architecture sim;
"""
    readme = f"""# {robot_name} — VHDL scaffold

1. Add `rtl/top.vhd` to your FPGA project and map the ports to real pins.
2. Implement the control law behind the TODO.
3. Simulate `tb/top_tb.vhd`, then synthesise for your target board.

This RTL is a scaffold; it does not implement a complete robotics controller.
"""
    return [
        CodeFile(path="rtl/top.vhd", language="vhdl", content=top, explanation="Top entity."),
        CodeFile(
            path="tb/top_tb.vhd", language="vhdl", content=testbench, explanation="Testbench."
        ),
        CodeFile(path="README.md", language="markdown", content=readme, explanation="FPGA steps."),
    ]


def _other_files(pins: dict[str, str], robot_name: str) -> list[CodeFile]:
    content = f"""# {robot_name} — language scaffold

Tell Albayraq which language and toolchain you want to use, then port
the generated pin map into your project.

## Pin map

```text
{chr(10).join(f"{name}: {pin}" for name, pin in pins.items()) or "No pins mapped."}
```

## Required behaviour

1. Initialise every mapped pin to a safe state.
2. Read the robot's sensors.
3. Compute a control output.
4. Stop all actuators when the loop exits or an error occurs.
"""
    return [
        CodeFile(
            path="README.md",
            language="markdown",
            content=content,
            explanation="Toolchain-neutral scaffold.",
        )
    ]


def _bundle(language: CodeLanguage, pins: dict[str, str], robot_name: str) -> LanguageBundle:
    builders = {
        CodeLanguage.PYTHON: _python_files,
        CodeLanguage.CPP: _cpp_files,
        CodeLanguage.C: _c_files,
        CodeLanguage.STM32_ASSEMBLY: _assembly_files,
        CodeLanguage.VERILOG: _verilog_files,
        CodeLanguage.VHDL: _vhdl_files,
        CodeLanguage.OTHER: _other_files,
    }
    libraries = {
        CodeLanguage.PYTHON: [],
        CodeLanguage.CPP: ["Arduino core"],
        CodeLanguage.C: ["STM32 HAL"],
        CodeLanguage.STM32_ASSEMBLY: [],
        CodeLanguage.VERILOG: [],
        CodeLanguage.VHDL: ["ieee.std_logic_1164"],
        CodeLanguage.OTHER: [],
    }
    notes = [
        "Generated from the validated electrical pin map.",
        "Scaffold only: complete the TODO blocks and verify every pin on hardware.",
    ]
    if language is CodeLanguage.C and not pins:
        notes.append("No controller pins were mapped; assign the MCU package before compiling.")
    return LanguageBundle(
        language=language,
        display_name=_DISPLAY[language],
        framework=_FRAMEWORK[language],
        status="scaffold",
        files=builders[language](pins, robot_name),
        libraries=libraries[language],
        notes=notes,
    )


class ProgrammingAgent(BaseAgent):
    """Generates multi-file starter bundles for every selected language."""

    name = AgentName.PROGRAMMING
    display_name = "Programming"
    description = (
        "Generates pin-mapped, multi-file firmware scaffolds for every selected "
        "language, with the controller's real pin assignments."
    )
    depends_on = (
        AgentName.PLANNER,
        AgentName.COMPONENT_RESEARCH,
        AgentName.ELECTRICAL,
    )
    input_model = ProgrammingInput
    output_model = ProgrammingOutput
    status = "available"
    milestone = "M6"
    owner_area = "AI Engineering / Firmware"

    async def execute(self, request: AgentRequest) -> ProgrammingOutput:
        specification = request.context.shared.specification
        research = request.context.shared.component_research
        electrical = request.context.shared.electrical
        if specification is None:
            raise ValueError("Programming requires a robot specification.")
        if research is None or electrical is None:
            raise ValueError("Programming requires the component BOM and electrical plan.")

        languages = _parsed_languages(request.parameters.get("languages"))
        pins = _pin_map(electrical)
        robot_name = request.context.project_name
        bundles = [_bundle(language, pins, robot_name) for language in languages]
        primary = bundles[0]

        setup_steps = [
            "Install the toolchain named in each bundle README.",
            "Compare every pin in the generated config against your board pinout.",
            "Complete the TODO blocks before connecting motors or high-current loads.",
        ]
        upload_steps = [
            "Compile the bundle and resolve any board-specific library errors.",
            "Flash or copy the files to the controller.",
            "Run at low power and verify the emergency stop path.",
        ]
        validation_notes = [
            "All pin names come from the electrical plan, not free-form generation.",
            "Generated code is untrusted scaffold input; review it before running.",
            "Unsupported languages are provided as structured scaffolds with explicit TODOs.",
        ]

        return ProgrammingOutput(
            platform=specification.target_platform,
            language=primary.language.value,
            framework=primary.framework,
            files=primary.files,
            bundles=bundles,
            libraries=sorted({library for bundle in bundles for library in bundle.libraries}),
            pin_assignments=pins,
            setup_steps=setup_steps,
            upload_steps=upload_steps,
            validation_notes=validation_notes,
        )


__all__ = ["ProgrammingAgent"]
