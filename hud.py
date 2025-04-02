# aircraft.py
import pygame
import math

WHITE = (255, 255, 255)

class Aircraft:
    def __init__(self, start_x, start_y, start_altitude):
        """Initializes the aircraft state."""
        self.x = start_x # Position on screen (center for this demo)
        self.y = start_y # Position on screen (center for this demo)
        self.altitude = start_altitude # Z-axis simulated (feet)
        self.pitch = 0 # Angle up/down (degrees)
        self.roll = 0 # Angle left/right bank (degrees)
        self.yaw = 0 # Heading (degrees) - Not fully used in rendering
        self.speed = 80 # Knots (arbitrary units here)
        self.vertical_speed = 0 # Feet per minute (simplified)

        self.throttle = 0.5 # 0.0 to 1.0

        # Control sensitivity
        self.pitch_rate = 20 # degrees per second
        self.roll_rate = 40  # degrees per second
        self.throttle_rate = 0.25 # throttle units per second

        # Simple physics constants (highly unrealistic)
        self.lift_factor = 0.015 # Adjusted for better feel
        self.drag_factor = 0.0006
        self.gravity = 9.8 * 3.28 # Approx ft/s^2 (used loosely)
        self.thrust_factor = 300 # Max thrust scaling
        self.stall_speed = 60 # Knots
        self.max_speed = 400 # Knots

        # Visual representation (simple triangle)
        self.base_image_orig = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.base_image_orig, WHITE, [(15, 0), (0, 40), (30, 40)])
        self.image = self.base_image_orig
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.is_crashed = False


    def update(self, dt, inputs):
        """Updates aircraft physics and state based on inputs and delta time."""
        if self.is_crashed:
            return

        # --- Apply Controls ---
        # Throttle
        if inputs['throttle_up']:
            self.throttle += self.throttle_rate * dt
        if inputs['throttle_down']:
            self.throttle -= self.throttle_rate * dt
        self.throttle = max(0.0, min(1.0, self.throttle)) # Clamp throttle

        # Pitch (Smoothed)
        target_pitch = self.pitch
        if inputs['pitch_up']: # Nose down (inverted controls often used)
            target_pitch += self.pitch_rate * dt
        if inputs['pitch_down']: # Nose up
            target_pitch -= self.pitch_rate * dt
        # Smoothly interpolate towards target pitch
        self.pitch += (target_pitch - self.pitch) * 5.0 * dt # Adjust smoothing factor
        self.pitch = max(-80.0, min(80.0, self.pitch)) # Limit pitch

        # Roll (Smoothed)
        target_roll = self.roll
        if inputs['roll_left']:
            target_roll += self.roll_rate * dt
        if inputs['roll_right']:
            target_roll -= self.roll_rate * dt
        # Auto-center roll slowly if no input
        if not inputs['roll_left'] and not inputs['roll_right']:
             target_roll = 0.0
        # Smoothly interpolate towards target roll
        self.roll += (target_roll - self.roll) * 6.0 * dt # Adjust smoothing factor
        self.roll = max(-80.0, min(80.0, self.roll)) # Limit roll


        # --- Simplified Physics ---
        # Speed based on throttle, pitch, and drag
        thrust = self.throttle * self.thrust_factor
        # Basic drag model (increases with square of speed)
        drag = self.speed * self.speed * self.drag_factor
        # Effect of pitch on speed (gravity component)
        pitch_effect_on_speed = math.sin(math.radians(self.pitch)) * self.gravity * 5 # Scaling factor

        acceleration = thrust - drag - pitch_effect_on_speed
        # Apply acceleration (adjust mass implicitly via scaling factor)
        self.speed += (acceleration / 50.0) * dt # '50.0' acts like mass/inertia
        self.speed = max(0, min(self.max_speed, self.speed))

        # Vertical Speed based on lift, gravity, and pitch component
        is_stalled = self.speed < self.stall_speed and self.altitude > 10 # Don't stall on ground

        # Simplified Lift model - proportional to square of speed and angle of attack (approximated by pitch cosine)
        # Angle of attack isn't really simulated here, using pitch as a proxy.
        lift_coefficient = 1.0 - abs(math.sin(math.radians(self.pitch))) # Max lift near 0 pitch, less when pitched up/down heavily
        lift = (self.speed * self.speed * self.lift_factor * lift_coefficient)

        # Vertical component of thrust/direction
        vertical_thrust_component = self.speed * math.sin(math.radians(-self.pitch)) * 5 # Scaling factor

        if not is_stalled:
            # Calculate change in vertical speed (Lift vs Gravity)
            vertical_acceleration = (lift - self.gravity*10) # '10' acts like mass/weight
            self.vertical_speed += vertical_acceleration * dt * 0.5 # Scaling/damping
            self.vertical_speed += vertical_thrust_component * dt # Add speed component from pitch direction
        else:
            # Stall behavior - drastically reduce lift, increase effect of gravity
            self.vertical_speed -= self.gravity * 3.0 * dt # Exaggerated gravity effect during stall

        # Apply some air resistance/damping to vertical speed
        self.vertical_speed *= (1.0 - 0.2 * dt)

        # Update Altitude
        self.altitude += self.vertical_speed * dt


        # --- Ground Collision / Landing ---
        if self.altitude <= 0:
            self.altitude = 0
            # Crash condition (vertical speed too high or roll too much)
            if abs(self.vertical_speed) > 300 or abs(self.roll) > 30:
                 print(f"CRASH! V/S: {int(self.vertical_speed)} fpm, Roll: {int(self.roll)} deg")
                 self.is_crashed = True
                 self.speed = 0
                 self.vertical_speed = 0
            else:
                 # Successful landing (or just stopped falling)
                 self.vertical_speed = 0
                 # Apply ground friction
                 self.speed *= (1.0 - 2.0 * dt)
                 if self.speed < 1: self.speed = 0


        # --- Update Visuals ---
        # Rotate image based on roll
        rotated_image = pygame.transform.rotate(self.base_image_orig, self.roll)
        new_rect = rotated_image.get_rect(center=self.rect.center)

        # We don't scale based on altitude here to keep it simpler
        self.image = rotated_image
        # Position on screen - slightly offset by pitch for visual cue
        self.rect = self.image.get_rect(center=(self.x, self.y - int(self.pitch * 1.5)))


    def draw(self, surface):
        """Draws the aircraft onto the surface."""
        if not self.is_crashed:
            surface.blit(self.image, self.rect)
        else:
            # Optional: Draw a crash marker or message
            pass

    def get_state(self):
      """Returns a dictionary of the current aircraft state for the HUD."""
      return {
          "speed": self.speed,
          "altitude": self.altitude,
          "vertical_speed": self.vertical_speed,
          "throttle": self.throttle,
          "pitch": self.pitch,
          "roll": self.roll,
          "is_stalled": self.speed < self.stall_speed and self.altitude > 10,
          "is_crashed": self.is_crashed
      }
