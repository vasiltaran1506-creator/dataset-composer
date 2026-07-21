# Dataset Composer UI Design System

> Version: 1.0 (Draft)

---

# Table of Contents

1. Introduction
2. Product Philosophy
3. UI Philosophy
4. Design Principles
5. Visual Language
6. Component Library
7. Workspace Design
8. Motion System & Interaction Guidelines
9. Accessibility
10. Future Directions
11. Design Tokens
12. Appendix

---

# 1. Introduction

## 1.1 Purpose

Dataset Composer is a professional desktop application for creating, organizing and maintaining high-quality datasets used in AI image generation.

Unlike traditional tagging tools, Dataset Composer is designed around the complete creative workflow — from character definition and scene composition to dataset generation and analysis.

This document defines the visual language, interaction principles and design rules used throughout the entire application.

Its purpose is to ensure that every screen, every component and every future feature share a common design philosophy.

This document serves as the single source of truth for the user interface.

---

## 1.2 Goals

The Dataset Composer interface should satisfy four primary goals:

- maximize productivity during long editing sessions;
- reduce cognitive load;
- encourage creative exploration;
- maintain visual consistency across the entire application.

Every design decision should contribute to at least one of these goals.

---

# 2. Product Philosophy

## 2.1 Scene-Centric Workflow

Dataset Composer is built around scenes.

A scene is the central creative unit of the application.

Characters, outfits, poses, environments, emotions, lighting, camera settings and every other element exist to construct complete, coherent scenes.

The application should therefore encourage users to think in terms of scene composition rather than isolated tags or configuration files.

Whenever possible, the interface should present data as meaningful building blocks of a scene.

---

## 2.2 Creative Workflow

Dataset creation is a creative process rather than a technical procedure.

The interface should reinforce this mindset.

Users should feel that they are designing, organizing and refining creative assets—not editing structured data.

Technical complexity should remain hidden behind intuitive interactions.

---

## 2.3 Long-Term Scalability

Dataset Composer is designed as an extensible ecosystem.

New workspaces, tools and features should integrate naturally into the existing interface without requiring a redesign.

The design system must therefore prioritize flexibility, modularity and consistency.

---

# 3. UI Philosophy

## 3.1 Calm Professionalism

Dataset Composer should feel professional without becoming intimidating.

The interface should communicate confidence through clarity rather than visual complexity.

Large amounts of information should remain approachable.

---

## 3.2 Invisible Interface

The interface exists to support creativity.

It should never compete with the user's content.

Visual decoration should be kept to a minimum.

Content always takes priority.

---

## 3.3 Living Interface

The interface should feel responsive and alive.

Every interaction should receive immediate visual feedback.

Hover states, smooth transitions and subtle animations should make the application feel tactile without becoming distracting.

Motion exists to explain interaction, not to decorate it.

---

## 3.4 Workspace-Oriented Design

Each major section of the application represents a dedicated workspace with its own purpose.

Examples include:

- Profiles
- Library
- Generate
- Analyzer
- Settings

Although each workspace serves different tasks, all of them should share the same visual language, interaction patterns and component library.

Users should never feel that they have entered a different application.

---

# 4. Design Principles

The following principles guide every interface decision.

---

## Principle 1 — Content First

The user's work is always the primary focus.

The interface should support the content rather than compete with it.

Visual decoration must remain secondary.

---

## Principle 2 — Cards Instead of Tables

Information should be grouped into visually independent sections whenever possible.

Cards create natural hierarchy while remaining easier to understand than traditional desktop tables.

---

## Principle 3 — Accordions Instead of Trees

Large expandable trees introduce unnecessary visual complexity.

Accordion-based organization provides a cleaner and more approachable experience.

Only currently relevant information should remain expanded.

---

## Principle 4 — Progressive Disclosure

Users should never be overwhelmed.

Information should appear gradually as it becomes relevant.

Advanced functionality should reveal itself naturally during the workflow.

---

## Principle 5 — Large Click Targets

Controls should never require precise cursor placement.

Entire rows should be interactive whenever possible.

Comfort takes priority over compactness.

---

## Principle 6 — Motion Explains Change

Animation communicates state changes.

Expanding, collapsing, selecting and loading should all be visually explained through motion.

Animation should never exist purely for decoration.

---

## Principle 7 — Consistency Above All

Every component should behave identically throughout the application.

Users should never need to relearn interactions between different workspaces.

Consistency reduces cognitive load and builds confidence.

---

## Principle 8 — Timeless Design

The interface should avoid short-lived design trends.

The goal is not to appear fashionable for one year, but modern for many years.

Every visual decision should prioritize longevity over novelty.

---

# 5. Visual Language

The visual language defines the fundamental building blocks of the Dataset Composer interface.

Every workspace, component and future feature should be constructed using the same visual rules.

The goal is to create a unified visual identity that remains recognizable regardless of which part of the application the user is currently working in.

---

# 5.1 Overall Visual Style

Dataset Composer should not resemble a traditional Qt application.

It should also avoid looking like a web application simply placed inside a desktop window.

Instead, the interface should combine the clarity of professional development tools with the warmth of modern creative software.

The desired visual impression is:

- calm;
- modern;
- professional;
- spacious;
- responsive;
- elegant.

The interface should feel visually lightweight while remaining information-dense.

---

# 5.2 Color Philosophy

Colors are used to communicate hierarchy rather than decoration.

The interface should rely on a small, carefully selected palette.

Avoid excessive variation between panels.

Depth should be created through subtle brightness differences instead of strong borders or shadows.

The application should avoid pure black backgrounds.

Instead, use cool graphite tones with a subtle blue tint.

This creates a softer and more comfortable appearance during long work sessions.

Accent colors should be used sparingly.

Only interactive elements should receive accent colors.

Neutral content should remain neutral.

---

# 5.3 Color Roles

Instead of assigning colors directly to widgets, the interface should define semantic color roles.

Examples include:

- Window Background
- Workspace Background
- Sidebar Background
- Card Background
- Elevated Card Background
- Hover Surface
- Pressed Surface
- Border
- Divider
- Primary Text
- Secondary Text
- Disabled Text
- Accent
- Accent Hover
- Accent Pressed
- Success
- Warning
- Error
- Selection
- Focus Ring

Individual colors may evolve over time.

Color roles should remain stable.

---

# 5.4 Visual Hierarchy

The interface should communicate hierarchy primarily through spacing and typography.

Borders should be considered a last resort.

The preferred order of visual separation is:

1. spacing;
2. typography;
3. contrast;
4. subtle background changes;
5. dividers;
6. borders.

Large sections should be separated by whitespace whenever possible.

---

# 5.5 Layout Philosophy

Every screen should be composed of large logical blocks.

Users should perceive the interface as a collection of meaningful work areas rather than dozens of individual widgets.

Each workspace should naturally guide the eye from top to bottom and from left to right.

Avoid creating unnecessary visual fragmentation.

---

# 5.6 Grid System

The entire application should follow a consistent spacing system.

Base spacing unit:

4 px

Preferred spacing values:

- 4 px
- 8 px
- 12 px
- 16 px
- 24 px
- 32 px
- 48 px

Avoid arbitrary spacing values.

Every margin, padding and gap should be derived from this scale.

Consistency creates rhythm.

---

# 5.7 Corner Radius

Rounded corners are a defining characteristic of the Dataset Composer visual identity.

Different components should not invent their own corner radius.

Recommended values:

- Small elements: 8 px
- Buttons and inputs: 10 px
- Cards: 12 px
- Dialogs: 14 px
- Chips: fully rounded

The interface should feel cohesive.

---

# 5.8 Borders

Borders should be subtle.

Avoid thick outlines.

Most sections should be separated using whitespace instead of visible borders.

Borders should primarily indicate:

- editable controls;
- selected states;
- keyboard focus;
- drag-and-drop targets.

Cards should not rely on strong borders to stand out.

---

# 5.9 Shadows

Shadows should be used sparingly.

Most elevation should be achieved through brightness rather than shadow.

Only floating elements may receive soft shadows.

Examples:

- context menus;
- dialogs;
- popups;
- floating previews.

Regular cards should remain visually flat.

---

# 5.10 Typography

Typography is the primary tool for creating hierarchy.

Text should never rely solely on bold weight.

Hierarchy should be established through size, spacing and contrast.

Recommended hierarchy:

Window Title

Largest text in the interface.

Section Title

Used for workspace headings.

Category Title

Used inside cards and accordions.

Body Text

Default readable content.

Secondary Text

Descriptions and supporting information.

Caption

Metadata and helper labels.

Avoid excessively small fonts.

Long editing sessions should remain comfortable.

---

# 5.11 Text Alignment

Text should be left-aligned by default.

Centered text should only be used when the component itself is centered.

Avoid inconsistent alignment between similar components.

Labels and descriptions should form clean vertical lines.

---

# 5.12 Icons

The application should use a single icon family.

Mixing icon styles is prohibited.

Icons should:

- be simple;
- be lightweight;
- use consistent stroke width;
- remain visually neutral.

Icons exist to support recognition.

They should never become decorative illustrations.

---

# 5.13 Whitespace

Whitespace is an active design element.

Empty space improves readability.

Avoid filling every available pixel.

Generous spacing should separate major sections.

Compact spacing should group related controls.

The interface should breathe.

---

# 5.14 Visual Rhythm

The application should establish a predictable rhythm.

Users should subconsciously recognize repeated patterns.

Examples:

Heading

↓

Description

↓

Primary Action

↓

Content

↓

Footer

Repeating structures reduce cognitive effort.

---

# 5.15 Information Density

The interface should support large amounts of information without appearing crowded.

Whenever density increases, spacing should remain consistent.

Never reduce readability simply to display more controls.

The goal is efficient navigation, not maximum compression.

---

# 5.16 Responsive Desktop Layout

Although Dataset Composer is a desktop application, layouts should gracefully adapt to different window sizes.

Panels should resize naturally.

Cards should wrap intelligently.

Content should avoid unnecessary horizontal scrolling.

Only specialized editors may require fixed layouts.

---

# 5.17 Empty Space

Empty states are intentional.

An empty workspace should never feel broken.

Instead, it should invite the user to perform the next meaningful action.

Examples include:

- Create Character
- Add Outfit
- Import Images
- Generate Dataset

Empty space should guide, not confuse.

---

# 5.18 Visual Consistency

Every screen should immediately be recognizable as part of Dataset Composer.

A user switching between workspaces should never need to mentally adjust to a different visual language.

Consistency should always take precedence over introducing new visual ideas.

New components should extend the existing design language rather than replace it.

---

# 6. Component Library

The Component Library defines every reusable interface element used throughout Dataset Composer.

Every component should be designed once and reused consistently across the entire application.

New screens should be assembled from existing components whenever possible.

Creating visually different components for similar purposes is discouraged.

The Component Library is the foundation of the application's consistency.

---

# 6.1 Component Philosophy

Every component should satisfy the following principles:

- immediately understandable;
- visually lightweight;
- comfortable to interact with;
- keyboard accessible;
- reusable;
- animated consistently;
- responsive to user interaction.

Components should never expose Qt-specific appearance.

Dataset Composer should present its own visual language.

---

# 6.2 Buttons

Buttons represent intentional actions.

Buttons should clearly communicate their importance through hierarchy rather than size alone.

Dataset Composer defines five button types.

---

## Primary Button

Used for the most important action within a view.

Examples:

- Generate Dataset
- Save Character
- Import Images
- Create Scene

Only one primary button should exist within a local context whenever possible.

---

## Secondary Button

Represents common actions with lower visual priority.

Examples:

- Edit
- Duplicate
- Rename
- Export

---

## Ghost Button

A low-emphasis button.

Uses transparent background.

Appears mainly on hover or inside toolbars.

---

## Icon Button

Square button containing only an icon.

Must always provide a tooltip.

Should never become the primary action.

---

## Danger Button

Reserved for destructive actions.

Examples:

- Delete
- Remove
- Reset

Danger should always require explicit confirmation.

---

# 6.3 Cards

Cards are the primary structural element of Dataset Composer.

Cards replace traditional GroupBoxes and many table-based layouts.

Every card should feel like an independent workspace.

Cards may contain:

- title
- description
- actions
- content
- footer

Cards should maintain generous internal spacing.

Avoid dense layouts.

---

# 6.4 Accordions

Accordions organize related information.

They replace large expandable trees.

Each accordion consists of:

Header

↓

Optional description

↓

Selection counter

↓

Expandable content

Only relevant accordions should remain expanded.

Expansion should always animate smoothly.

---

# 6.5 Chips

Chips represent selected items.

Examples:

- selected tags
- applied filters
- active categories

Chips should remain compact while preserving comfortable click areas.

Every removable chip should contain a dedicated remove action.

The remove action should appear naturally without overwhelming the component.

Chips should wrap automatically.

Overflow should never produce horizontal scrolling.

---

# 6.6 Search Field

Search is a global interaction component.

Search fields should:

- support instant filtering;
- provide immediate feedback;
- include clear action;
- display placeholder text;
- animate focus state.

Whenever search is active, unrelated interface elements should visually recede.

Search results become the primary content.

---

# 6.7 Check Rows

Traditional checkboxes should not be presented in isolation.

Instead, Dataset Composer introduces Check Rows.

A Check Row consists of:

Selection indicator

↓

Primary label

↓

Optional description

↓

Optional metadata

The entire row is clickable.

Hover affects the entire row.

Selection changes the appearance of the entire component rather than only the checkbox.

---

# 6.8 Input Fields

Input fields should remain visually simple.

Every field should clearly communicate:

- editable
- focused
- disabled
- invalid

Validation should never rely exclusively on color.

---

# 6.9 Dropdowns

Dropdowns should display meaningful values rather than internal identifiers.

Menus should remain visually lightweight.

Avoid excessive nesting.

Long lists should support search.

---

# 6.10 Toggle Controls

Toggle switches should represent persistent application state.

Checkboxes represent item selection.

These concepts should never be mixed.

---

# 6.11 Tabs

Tabs define navigation between workspaces.

Workspace tabs should remain visually stable.

Switching tabs should never reset user context unnecessarily.

The active tab should be immediately recognizable.

---

# 6.12 Sidebar

The sidebar provides navigation.

It should remain calm and visually unobtrusive.

Items support:

- hover
- active state
- context menu
- drag-and-drop (where applicable)

The sidebar should prioritize readability over density.

---

# 6.13 Toolbars

Toolbars expose frequently used actions.

Avoid placing rarely used controls inside toolbars.

Toolbar actions should remain icon-first.

Text may appear inside tooltips.

---

# 6.14 Dialogs

Dialogs interrupt the workflow.

Use them sparingly.

Dialogs should always answer three questions:

What happened?

What does the user need to decide?

What happens next?

---

# 6.15 Notifications

Notifications should communicate progress without interrupting work.

Preferred order:

Toast

↓

Inline Message

↓

Modal Dialog

Modal dialogs should be reserved for situations requiring immediate attention.

---

# 6.16 Empty States

Every workspace should define meaningful empty states.

An empty workspace should explain:

- why it is empty;
- what the user can do next;
- which action is recommended.

Whenever appropriate, provide a direct action button.

---

# 6.17 Loading States

Loading should never freeze the interface.

Whenever possible:

- display progress;
- preserve layout;
- avoid sudden content jumps.

Skeleton placeholders are preferred over empty panels.

---

# 6.18 Context Menus

Context menus expose secondary functionality.

Primary actions should never be hidden exclusively inside context menus.

Context menus should remain concise.

Avoid creating long hierarchical menus.

---

# 6.19 Tooltips

Tooltips supplement the interface.

They should explain.

They should never compensate for poor design.

If every control requires a tooltip, the interface itself should be reconsidered.

---

# 6.20 Component States

Every interactive component should define consistent states.

Minimum required states:

- Default
- Hover
- Pressed
- Focused
- Selected
- Disabled
- Loading
- Error (where applicable)

State transitions should animate consistently throughout the application.

---

# 7. Workspace Design

Each major section of Dataset Composer represents an independent workspace.

A workspace is not merely a page within the application.

It is an environment optimized for completing a specific creative task.

Although every workspace serves a different purpose, they all share the same visual language, component library and interaction principles.

Every workspace should answer three questions within the first few seconds:

- Where am I?
- What can I do here?
- What should I do next?

---

# 7.1 General Workspace Structure

Every workspace should follow the same high-level layout.

```
┌──────────────────────────────────────────────────────────────────────┐
│ Top Navigation                                                       │
├──────────────┬────────────────────────────────────┬──────────────────┤
│              │                                    │                  │
│              │                                    │                  │
│ Navigation   │         Main Workspace             │  Context Panel   │
│              │                                    │                  │
│              │                                    │                  │
├──────────────┴────────────────────────────────────┴──────────────────┤
│ Status Bar (optional)                                                │
└──────────────────────────────────────────────────────────────────────┘
```

This layout should remain recognizable throughout the application.

Users should never feel disoriented when switching workspaces.

---

# 7.2 Workspace Header

Every workspace begins with a header.

The header establishes context.

It should contain:

- workspace title;
- short description;
- optional primary action;
- optional statistics.

The header should remain visually lightweight.

Large decorative banners are discouraged.

---

# 7.3 Primary Content Area

The center of every workspace contains the primary content.

This area always receives the highest visual priority.

It should never compete with side panels or toolbars.

Whenever possible, content should be organized into cards rather than long continuous layouts.

---

# 7.4 Context Panel

The right panel provides contextual information.

Unlike the main workspace, it does not define the workflow.

Instead, it supports it.

Examples include:

- character portrait;
- metadata;
- quick statistics;
- validation messages;
- selection summary;
- preview;
- history.

The context panel should update dynamically based on the user's current selection.

---

# 7.5 Navigation

Navigation should remain visually quiet.

Its purpose is orientation rather than attracting attention.

Navigation elements should support:

- hover;
- active state;
- keyboard navigation;
- drag-and-drop where appropriate.

---

# 7.6 Workspace Identity

Every workspace should have its own personality.

This personality should emerge through layout and content—not through different colors or visual styles.

Consistency always takes priority over uniqueness.

---

# Profiles Workspace


# 7.7 Profiles Workspace

Purpose

The Profiles workspace is the heart of Dataset Composer.

Its purpose is to help users construct complete, coherent character profiles.

The workspace should encourage exploration rather than checklist completion.

Users should feel that they are shaping a character rather than editing metadata.

---

Primary User Goal

"I want to define who this character is."

---

Visual Priority

The user's attention should naturally flow in the following order:

1. Character identity
2. Current selections
3. Search
4. Editable categories
5. Context information

---

Recommended Layout


Character Name

Short Description

────────────────────────────────────────────

Selected Traits

[ Brown Eyes ] [ Petite ] [ Round Face ]

────────────────────────────────────────────

Search

────────────────────────────────────────────

Appearance

▼ Face

▼ Hair

▼ Eyes

▼ Body

▼ Expressions


Categories should be represented as accordion cards.

Each category should feel like a self-contained editing space.

Large trees should be avoided.

---

Context Panel

The context panel may contain:

- character portrait;
- profile summary;
- completion progress;
- statistics;
- notes.

Portraits are user-provided rather than AI-generated.

The interface should support future expansion without requiring redesign.

---

Editing Experience

Selecting traits should feel lightweight.

Entire rows should be clickable.

Changes should be reflected immediately.

Selections should update smoothly.

The interface should reward experimentation.

---

# 7.8 Library Workspace

Purpose

The Library workspace manages reusable assets.

Unlike Profiles, this workspace focuses on exploration rather than editing.

---

Primary User Goal

"I want to quickly find the asset I need."

---

Visual Priority

Search

↓

Filters

↓

Content

↓

Details

---

Layout


Search

Filters

────────────────────────────

Cards

Cards

Cards

Cards


Large visual previews should be preferred whenever available.

Metadata should remain secondary.

The Library should feel like browsing a curated collection rather than a filesystem.

---

# 7.9 Generate Workspace

Purpose

The Generate workspace transforms creative work into output.

Its design should emphasize progress and confidence.

---

Primary User Goal

"I am ready to generate my dataset."

---

Visual Priority

Generate Button

↓

Progress

↓

Logs

↓

Results

---

The Generate workspace should feel focused.

Avoid unnecessary controls.

Generation is an action-oriented workflow.

The interface should reinforce this mindset.

---

# 7.10 Analyzer Workspace

Purpose

The Analyzer workspace helps users understand the quality of their datasets.

Unlike the Generate workspace, Analyzer is exploratory.

Users investigate rather than produce.

---

Primary User Goal

"I want to understand what is missing."

---

Preferred Components

Cards

Charts

Coverage indicators

Statistics

Validation summaries

Missing data lists

Future recommendations

---

The Analyzer should answer questions rather than merely display numbers.

Visualization should always communicate insight.

---

# 7.11 Settings Workspace

Purpose

Settings configure the application itself.

This workspace should remain intentionally minimal.

Avoid unnecessary visual decoration.

---

Primary User Goal

"I want to change a setting and immediately return to work."

---

Settings should be grouped into logical categories.

Long scrolling pages should be avoided.

Search should always be available.

---

# 7.12 Workspace Consistency

Every workspace should feel familiar.

Regardless of the task being performed, users should always recognize:

- the same spacing;
- the same typography;
- the same cards;
- the same animations;
- the same navigation patterns;
- the same interaction principles.

Switching workspaces should feel like changing rooms within the same building—not entering a different application.

Consistency builds confidence.

Confidence increases productivity.

---

# 8. Motion System & Interaction Guidelines

Motion is a functional part of the Dataset Composer interface.

Animations are not decorative.

Their primary purpose is to communicate state changes, preserve spatial continuity and provide immediate feedback.

Every animation should answer one question:

> "What just happened?"

If an animation does not improve understanding, it should not exist.

---

# 8.0 Behavior Blueprint Methodology

The Motion System is built on a single guiding idea: every interactive component must have a precisely defined sequence of visual reactions to user input.

This sequence is called a **Behavior Blueprint**.

Instead of describing components with vague adjectives like "smooth" or "responsive", every component in Dataset Composer is defined frame-by-frame. This removes ambiguity between design and implementation and guarantees that the final interface feels consistent and intentional.

---

## Why Blueprints

A typical design system stops at listing component states:

- Default
- Hover
- Pressed
- Focused
- Disabled

This is insufficient. It describes *what* a component looks like, but not *how it gets there* and *in what order*.

A Behavior Blueprint describes the component's **character** — the timing, easing and sequence of reactions that make it feel alive. Two components with identical static states can feel completely different if their blueprints differ.

> A component's behavior is part of its identity.

---

## Blueprint Structure

Every Behavior Blueprint follows the same timeline template. This uniform structure allows designers, developers and future contributors to scan any component's behavior in seconds.

Default
↓
Hover-In (what changes, duration, easing)
↓
Hover-Hold (what remains visible while cursor stays)
↓
Hover-Out (what retracts, duration, easing)
↓
Press (tactile feedback, duration)
↓
Release (return or commit)
↓
Focus (keyboard navigation state)
↓
Disabled (where applicable)
↓
Expand/Collapse (for accordion-like components only)


Each step specifies:
- **What** changes visually (background, elevation, icon, border, scale, opacity, color).
- **How long** the transition takes, referencing the timing groups defined in `8.2 Animation Timing`.
- **How** the transition accelerates/decelerates (easing curve).

---

## Blueprint Placement Rule

Static descriptions live in **Chapter 6 (Component Library)**.
Dynamic behavior lives in **Chapter 8 (Motion System)**.

Every component section in Chapter 6 ends with a short cross-reference:

> *Behavior → §8.X*

The full Behavior Blueprint is defined only in Chapter 8. This separation keeps Chapter 6 focused on anatomy and semantics, while Chapter 8 owns motion and timing.

---

## Blueprint Checklist

Before a component is considered complete, its Behavior Blueprint must explicitly answer:

1. What happens when the cursor enters?
2. What remains visible while hovering?
3. What retracts when the cursor leaves?
4. What happens on press?
5. What happens on release?
6. How does keyboard focus manifest?
7. Does the component have an expand/collapse behavior? If yes, how is it animated?
8. How does the component communicate its disabled state?
9. Does the component participate in a transition (tab switch, workspace change)?

Any component that leaves one of these questions unanswered is not production-ready.

---

# 8.1 Motion Principles

Every animation should follow these principles.

## Immediate

User actions should receive visual feedback instantly.

The interface should never appear unresponsive.

---

## Natural

Motion should resemble physical movement.

Acceleration and deceleration should feel smooth.

Linear motion should be avoided whenever possible.

---

## Subtle

Animations should support the workflow.

They should never distract from it.

---

## Consistent

Animations should feel identical throughout the application.

A card should expand using the same visual language as an accordion.

Hover effects should behave consistently across all components.

---

## Purposeful

Every animation must communicate information.

Examples:

- a section expands;
- an item becomes selected;
- a search result appears;
- an operation finishes.

Animations should never exist purely because they "look cool."

---

# 8.2 Animation Timing

The interface should use a small set of predefined durations.

Recommended timing groups:

| Purpose | Duration |
|----------|----------|
| Hover | 120–160 ms |
| Selection | 140–180 ms |
| Press | 80–120 ms |
| Expand / Collapse | 180–220 ms |
| Dialog | 220–260 ms |
| Notifications | 200–250 ms |

Avoid arbitrary durations.

A consistent rhythm creates a predictable experience.

---

# 8.3 Hover Behavior

Hover is the primary communication channel between the interface and the user.

Every interactive element should acknowledge pointer presence.

Hover may include:

- subtle background transition;
- slight elevation;
- icon appearance;
- border emphasis;
- accent color transition.

Hover should never dramatically change layout.

---

# 8.4 Pressed State

Pressing a control should feel tactile.

Preferred effects include:

- slight scale reduction;
- darker background;
- reduced elevation.

The pressed state should disappear immediately after release.

---

# 8.5 Focus State

Keyboard navigation must remain visually clear.

Focused elements should display a dedicated focus indicator.

Focus should never rely solely on color.

The indicator should remain elegant and unobtrusive.

---

# 8.6 Selection

Selection represents commitment.

Selected components should communicate:

- confidence;
- clarity;
- persistence.

Selection should affect the entire component.

Avoid changing only the checkbox.

Examples:

- selected rows;
- selected chips;
- selected cards;
- selected categories.

---

# 8.7 Expand & Collapse

Expandable components should preserve spatial continuity.

The user should always understand where new content appears.

Expansion should:

- smoothly increase height;
- reveal content gradually;
- preserve surrounding layout.

Content should never abruptly appear.

---

# 8.8 Search Interaction

Search should feel immediate.

Every keystroke should produce visible feedback.

Filtering should animate naturally.

Results should smoothly appear and disappear.

Avoid flashing layouts.

---

# 8.9 Card Interaction

Cards are one of the primary interaction surfaces.

Cards should communicate three levels of interaction.

Default

↓

Hover

↓

Selected

Hover may include:

- lighter surface;
- soft elevation;
- action buttons fading in.

Selected cards should clearly indicate their state while remaining visually calm.

---

# 8.10 Accordion Interaction

Accordion headers should clearly communicate interactivity.

Hover:

- slight background transition.

Click:

- smooth expansion.

Expanded:

- rotated disclosure icon;
- animated content reveal.

Counters should update immediately.

---

# 8.11 Chip Interaction

Chips should feel lightweight.

Hover:

- brighter background.

Remove button:

- fade in.

Pressed:

- slight compression.

Removing a chip should animate.

Neighbouring chips should reposition smoothly.

---

# 8.12 Check Row Interaction

Dataset Composer replaces isolated checkboxes with interactive rows.

Hover:

The entire row highlights.

Click:

Selection indicator animates.

Background changes.

Optional accent bar appears.

Selection should never feel limited to the checkbox itself.

---

# 8.13 Context Panel Updates

The context panel should update dynamically.

Content changes should use fade transitions.

Avoid replacing large sections instantly.

Maintain continuity.

---

# 8.14 Loading States

Loading should preserve layout stability.

Preferred approach:

Skeleton placeholders

↓

Content fades in

↓

Interactive controls become available

Avoid:

- jumping layouts;
- flashing controls;
- empty white spaces.

---

# 8.15 Empty States

Empty states should never feel unfinished.

Each empty state should explain:

Why is this empty?

↓

What can I do?

↓

Primary Action

Illustrations may be used sparingly.

The emphasis should remain on guidance rather than decoration.

---

# 8.16 Notifications

Notifications should remain unobtrusive.

Preferred order:

Information

↓

Success

↓

Warning

↓

Error

Toast notifications should disappear automatically when appropriate.

Critical errors require explicit acknowledgement.

---

# 8.17 Progress

Progress indicators should communicate continuous activity.

Whenever possible:

Show percentage.

Show current task.

Show estimated remaining work.

Long operations should never appear frozen.

---

# 8.18 Drag & Drop

Dragging should feel physical.

Dragged objects should slightly detach from the interface.

Valid drop targets should highlight naturally.

Invalid targets should remain visually calm.

Drop completion should animate.

---

# 8.19 Workspace Transitions

Switching between workspaces should preserve orientation.

Avoid dramatic transitions.

Recommended:

Short fade.

Subtle content slide.

Persistent navigation.

The application should feel continuous.

---

# 8.20 Error Presentation

Errors should explain.

Never simply display:

"Operation failed."

Instead communicate:

What happened.

↓

Why it happened.

↓

How to fix it.

↓

Optional details.

Users should always leave an error message with a clear next step.

---

# 8.21 Interaction Quality Checklist

Every interactive component should satisfy the following checklist.

✓ Hover feedback

✓ Press feedback

✓ Keyboard support

✓ Focus state

✓ Disabled state

✓ Loading state (if applicable)

✓ Animated transitions

✓ Accessible click target

✓ Consistent spacing

✓ Consistent timing

Components that do not satisfy this checklist should not be considered complete.

---

# 8.22 Behavior Blueprints for Core Components

To ensure absolute consistency between design and implementation, every interactive component must have a precisely defined sequence of visual reactions to user input. This sequence is called a **Behavior Blueprint**.

Instead of describing components with vague adjectives, every component is defined frame-by-frame. This removes ambiguity and guarantees that the final interface feels cohesive, tactile, and intentional.

---

## 8.22.1 Button Behavior Blueprint

Dataset Composer defines five button types (see §6.2). Each type shares the same behavioral skeleton but differs in visual emphasis.

### Primary Button
- **Default**: Background is Accent color, text is white, no border. Cursor is pointer.
- **Hover-In (120 ms, ease-out)**: Background lightens to Accent Hover. Subtle elevation (1 px shadow) appears.
- **Hover-Hold**: State remains stable, no additional elements appear.
- **Hover-Out (120 ms, ease-in)**: Background returns to Accent, elevation fades out.
- **Press (80 ms, ease-in)**: Background darkens to Accent Pressed. Scale reduces to 97%. Elevation is removed.
- **Release (100 ms, ease-out)**: Returns to Hover state if cursor remains, or Default if cursor left during press.
- **Focus (keyboard)**: Visible focus ring appears outside the button boundary (Focus Ring token, 2 px width, 2 px offset).
- **Disabled**: Opacity drops to 40%. Cursor changes to not-allowed. No hover, press, or focus response.

### Secondary Button
- **Default**: Background is Card Background, text is Primary Text, 1 px solid Border.
- **Hover-In (120 ms, ease-out)**: Background transitions to Hover Surface. Border color subtly transitions toward Accent.
- **Press (80 ms, ease-in)**: Background transitions to Pressed Surface. Scale reduces to 97%.

### Ghost Button
- **Default**: Transparent background, Secondary Text color, no border.
- **Hover-In (120 ms, ease-out)**: Background fades in to Hover Surface. Text color transitions to Primary Text.
- **Hover-Out (120 ms, ease-in)**: Background fades out to transparent. Text returns to Secondary Text.
- **Press (80 ms, ease-in)**: Background transitions to Pressed Surface. No scale change to maintain lightweight feel.

### Icon Button
- **Default**: Transparent background, icon color is Secondary Text.
- **Hover-In (120 ms, ease-out)**: Background fades in to Hover Surface. Icon transitions to Primary Text. Tooltip appearance delay begins (400 ms).
- **Hover-Hold (after 400 ms)**: Tooltip appears with a fade-in (120 ms).
- **Hover-Out (120 ms, ease-in)**: Background fades out. Tooltip disappears immediately.

### Danger Button
- **Default**: Error color at 15% opacity, text is Error color, 1 px solid Error border at 30% opacity.
- **Hover-In (120 ms, ease-out)**: Background transitions to Error color at 25% opacity.
- **Press (80 ms, ease-in)**: Background transitions to Error color at 40% opacity. Scale reduces to 97%.
- **Release (100 ms, ease-out)**: Returns to Hover or Default depending on cursor position.

---

## 8.22.2 Input Field Behavior Blueprint

Input fields are the primary text entry surfaces. They must clearly communicate editability, focus, and validation state.

- **Default**: Background is Card Background, 1 px solid Border token, text is Primary Text, placeholder is Secondary Text.
- **Hover-In (120 ms, ease-out)**: Border color transitions to Accent at 50% opacity. Background remains unchanged.
- **Hover-Out (120 ms, ease-in)**: Border color returns to Border token.
- **Focus-In (140 ms, ease-out)**: Border transitions to Accent (full opacity). Focus ring appears outside the boundary (Accent at 30% opacity, 2 px width). Placeholder text fades out (100 ms). Cursor caret appears.
- **Typing**: Each character appears immediately (no animation). Background and border remain stable.
- **Focus-Out (140 ms, ease-in)**: Border returns to Border token. Focus ring fades out. If empty, placeholder fades back in (120 ms).
- **Invalid State**: Border transitions to Error (140 ms). Focus ring transitions to Error at 30% opacity. Error message appears below the field with a slide-down and fade-in (160 ms).
- **Invalid to Valid**: Border returns to Border token (140 ms). Error message slides up and fades out (160 ms).
- **Disabled**: Opacity 40%, background is Hover Surface, cursor is not-allowed. No hover or focus response.

---

## 8.22.3 Search Field Behavior Blueprint

Search fields behave like input fields but with additional filtering behavior. Search is always instant.

- **Default**: Identical to Input Field. Search icon visible on the left (Secondary Text). Clear button is hidden.
- **Focus-In (140 ms, ease-out)**: Identical to Input Field Focus-In. Search icon transitions to Accent color.
- **Typing**: Clear button fades in (100 ms) on the right side after the first character. Filtering begins after 80 ms debounce. Non-matching items in the target list fade out (120 ms) and collapse (height animates to zero over 160 ms).
- **Clear Button Press**: Text clears instantly. Clear button fades out (100 ms). All items in the target list fade back in (120 ms) and expand (160 ms). Search icon returns to Secondary Text.
- **Escape Key**: If text exists, behaves identically to Clear Button Press. If empty, focus leaves the search field.
- **Focus-Out (with text)**: Border returns to default. Filtered state persists.

---

## 8.22.4 Dropdown Behavior Blueprint

Dropdowns present a list of options. They should feel lightweight and respond quickly.

- **Default (Closed)**: Background is Card Background, 1 px solid Border. Chevron icon points right or down. Text shows current selection or placeholder.
- **Hover-In (120 ms, ease-out)**: Border transitions to Accent at 50% opacity.
- **Open (160 ms, ease-out)**: Border transitions to Accent (full). Chevron rotates 90 degrees (160 ms). Menu panel appears below with opacity 0 to 1 and translateY -4 px to 0 (160 ms). Menu panel has a soft shadow. Currently selected item is highlighted.
- **Hover over menu item (80 ms, ease-out)**: Item background transitions to Hover Surface.
- **Select item (140 ms, ease-in)**: Value updates instantly. Chevron rotates back (140 ms). Menu panel fades out and collapses (140 ms). Border returns to default.
- **Click outside / Escape (140 ms, ease-in)**: Value remains unchanged. Menu closes. Focus returns to the dropdown.
- **Disabled**: Opacity 40%, no interaction response.

---

## 8.22.5 Toggle Control Behavior Blueprint

Toggles represent persistent binary state. They must never be confused with momentary buttons.

- **Default (Off)**: Track background is Border token. Knob is positioned left. Knob color is Secondary Text.
- **Hover-In (120 ms, ease-out)**: Track background lightens by one step. Knob remains in position.
- **Click to On (180 ms, ease-in-out)**: Knob slides from left to right. Track transitions to Accent color. Knob color transitions to white. State commits immediately on click.
- **Hover-In while On (120 ms, ease-out)**: Track lightens to Accent Hover.
- **Click to Off (180 ms, ease-in-out)**: Knob slides right to left. Track transitions to Border token. Knob transitions to Secondary Text.
- **Focus (keyboard)**: Focus ring appears around the entire toggle (Accent at 30% opacity, 2 px, offset 2 px). Space bar toggles state with the same animation.
- **Disabled**: Opacity 40%, no interaction response.

---

## 8.22.6 Tab Behavior Blueprint

Tabs define navigation between workspaces. The active tab must be immediately recognizable without relying solely on color.

- **Default (Inactive)**: Transparent background, Secondary Text color. Bottom indicator is hidden (height 0).
- **Hover-In (120 ms, ease-out)**: Text transitions to Primary Text. Background transitions to Hover Surface. Bottom indicator remains hidden.
- **Hover-Out (120 ms, ease-in)**: Text returns to Secondary Text. Background returns to transparent.
- **Activation (180 ms, ease-out)**: Previously active tab text returns to Secondary Text (140 ms), bottom indicator shrinks to zero width from center (160 ms). Newly active tab text transitions to Primary Text (140 ms), bottom indicator expands from zero to full width (180 ms, ease-out). Indicator is Accent color, 2 px height.
- **Keyboard Navigation**: Arrow keys move focus. Focus ring is 2 px outline, Accent at 30% opacity. Enter/Space activates focused tab.
- **Tab with badge**: Counter animates scale (100% to 110% to 100%) when value changes (200 ms).

---

## 8.22.7 Sidebar Behavior Blueprint

The sidebar provides persistent navigation. It should feel calm and stable.

- **Default (Inactive)**: Transparent background, Secondary Text and Icon. Left accent bar is hidden (width 0).
- **Hover-In (120 ms, ease-out)**: Background transitions to Hover Surface. Text and Icon transition to Primary Text. Left accent bar remains hidden.
- **Hover-Out (120 ms, ease-in)**: All properties return to Default.
- **Activation (160 ms, ease-out)**: Previously active item returns to Default, left accent bar shrinks to zero height from center (140 ms). Newly active item background transitions to Elevated Card Background, text and icon transition to Primary Text, icon becomes Accent color. Left accent bar expands to full item height (160 ms, 3 px wide, Accent color).
- **Keyboard Navigation**: Arrow Up/Down moves focus. Enter/Space activates.

---

## 8.22.8 Dialog Behavior Blueprint

Dialogs interrupt the workflow and must justify their presence. They should appear decisively and dismiss cleanly.

- **Appear (220 ms, ease-out)**: Backdrop fades in (opacity 0 to 1, black at 40% opacity). Dialog panel scales from 96% to 100% and fades in (220 ms). Dialog has a soft shadow. Focus moves to the first interactive element. Focus trap activates.
- **Visible**: Dialog remains stable. Backdrop click dismisses (if not critical). Escape key dismisses (if not critical).
- **Dismiss (180 ms, ease-in)**: Dialog scales from 100% to 96% and fades out (180 ms). Backdrop fades out (180 ms). Focus returns to the trigger element.
- **Critical Dialog**: Backdrop click and Escape key do NOT dismiss. Only explicit button press dismisses.

---

## 8.22.9 Toast Notification Behavior Blueprint

Toasts communicate progress without interrupting work. They should be noticeable but never blocking.

- **Appear (200 ms, ease-out)**: Toast slides in from the right edge (translateX 20 px to 0, opacity 0 to 1). Soft shadow appears. Auto-dismiss timer begins (4000 ms for info/success, 6000 ms for warning, manual for error).
- **Visible**: Progress bar at the bottom shrinks from 100% to 0% over the duration. Hover pauses timer and freezes progress bar. Hover out resumes. Close button dismisses immediately.
- **Dismiss (160 ms, ease-in)**: Toast slides out to the right (translateX 0 to 20 px, opacity 1 to 0). Remaining toasts shift position to fill the gap (160 ms, ease-in-out).
- **Stacking**: Multiple toasts stack vertically with 8 px gap. New toasts appear at the top. Maximum visible is 3.

---

# 8.23 Card Behavior Blueprint (Extended)

Cards are one of the primary interaction surfaces. This blueprint extends the general Card Interaction guidelines (§8.9) with precise frame-by-frame timing and state specifications.

## Card — Default Variant
- **Default**: Background is Card Background. Border is 1 px solid Border token. Corner radius 12 px. Internal padding 16 px on all sides. No elevation.
- **Hover-In (140 ms, ease-out)**: Background lightens by one step to Hover Surface. Border color transitions toward Accent at 20% opacity. No scale change. Subtle elevation shadow appears (2 px blur, 0 opacity → 8% opacity, black).
- **Hover-Hold**: State remains stable. If the card contains secondary actions that were hidden, they fade in (120 ms) in the top-right corner.
- **Hover-Out (140 ms, ease-in)**: Background returns to Card Background. Border returns to Border token. Shadow fades out. Hidden actions fade out.
- **Press (80 ms, ease-in)**: Scale reduces to 98%. Background darkens to Pressed Surface. Shadow disappears.
- **Release (100 ms, ease-out)**: Returns to Hover state if cursor remains, or Default if cursor left during press.
- **Focus (keyboard)**: Focus ring appears 2 px outside the card boundary. Color: Focus Ring token (Accent at 30% opacity). Offset: 2 px from card edge.
- **Selected**: Background transitions to Elevated Card Background (180 ms). Left accent bar (3 px wide, Accent color) fades in along the left edge. Border transitions to Accent at 50% opacity.
- **Disabled**: Opacity drops to 40%. Cursor changes to not-allowed. No hover, press, or focus response.

## Card — Clickable Variant
Identical to Default Variant with the following additions:
- **Default**: Cursor is pointer throughout the card area.
- **Click (180 ms, ease-out)**: Card transitions to Selected state. Selection is committed immediately on press.
- **Double-Click**: Triggers the card's primary action (e.g., open detail view). No visual animation — the primary action handles the transition.

## Card — Expandable Variant
- **Default**: Chevron icon on the right points right (or down depending on orientation).
- **Click (220 ms, ease-in-out)**: Chevron rotates 90 degrees. Card content area smoothly expands from height 0 to natural height. Content fades in (160 ms, starting 60 ms after expansion begins).
- **Collapse (200 ms, ease-in-out)**: Content fades out (120 ms, first half). Height collapses to 0 (200 ms, second half). Chevron rotates back.

> Behavior → Applies to: Cards (§6.3)

---

# 8.24 Accordion Behavior Blueprint

Accordions organize related information into collapsible sections. This blueprint extends §8.10 with detailed state specifications.

## Accordion Header
- **Default**: Background is transparent. Padding 12 px vertical, 16 px horizontal. Chevron icon points right. Title text is Category Title style. Optional counter badge on the right.
- **Hover-In (120 ms, ease-out)**: Background transitions to Hover Surface. Chevron color transitions to Primary Text. Title text color remains unchanged. Counter badge remains unchanged.
- **Hover-Hold**: State remains stable.
- **Hover-Out (120 ms, ease-in)**: Background returns to transparent. Chevron returns to Secondary Text.
- **Press (80 ms, ease-in)**: Background darkens to Pressed Surface. No scale change.
- **Release (100 ms, ease-out)**: Triggers expansion or collapse animation.

## Accordion Expansion
- **Expand (220 ms, ease-in-out)**: Chevron rotates 90 degrees clockwise (220 ms). Content area smoothly increases height from 0 to natural height (220 ms). Content fades in (160 ms, starting 60 ms after expansion begins). Surrounding content smoothly shifts downward — no layout jumps.
- **Collapse (200 ms, ease-in-out)**: Content fades out (120 ms, first half of animation). Chevron rotates 90 degrees counterclockwise (200 ms). Height collapses to 0 (200 ms, second half of animation). Surrounding content smoothly shifts upward.

## Accordion Counter Badge
- **Default**: Small chip showing `N selected` or `N / M`. Background is Accent at 15% opacity. Text is Accent color. Corner radius fully rounded. Padding 2 px vertical, 8 px horizontal.
- **Value Change (200 ms, ease-out)**: When the counter value changes, the badge animates scale (100% → 110% → 100%). Background flashes to Accent at 25% opacity for 100 ms, then returns to 15%.

## Accordion Category Card (Dataset Composer variant)
This variant is used specifically in the Profiles workspace for DNA categories. It combines accordion behavior with card visuals.
- **Default**: Background is Card Background. Left side contains a colored square icon badge (16 px × 16 px, rounded 4 px, filled with category color). Title with description subtitle. Right side shows counter badge and chevron.
- **Hover-In (140 ms, ease-out)**: Background lightens to Hover Surface. Icon badge slightly brightens. Subtle elevation appears.
- **Expand (220 ms, ease-in-out)**: Accordion expansion behavior applies. Additionally, a left accent bar (3 px wide, category color) fades in along the left edge.
- **Expanded State**: Content area displays Check Row grid. Background remains Card Background. Internal padding 16 px.

> Behavior → Applies to: Accordions (§6.4)

---

# 8.25 Chip Behavior Blueprint

Chips represent selected items. Dataset Composer uses two distinct chip modes. This blueprint defines both.

## Chip — Default (Wrap Mode)
Used in most contexts. Chips wrap to multiple lines as needed.
- **Default**: Background is Accent at 15% opacity. Text is Primary Text. Corner radius fully rounded. Padding 4 px vertical, 12 px horizontal. Remove button (×) hidden by default.
- **Hover-In (120 ms, ease-out)**: Background transitions to Accent at 25% opacity. Remove button fades in on the right side (100 ms). Cursor changes to pointer over the entire chip.
- **Hover-Out (120 ms, ease-in)**: Background returns to Accent at 15% opacity. Remove button fades out.
- **Press on chip body (80 ms, ease-in)**: Background darkens to Accent at 35% opacity. Scale reduces to 97%.
- **Press on remove button (80 ms, ease-in)**: Remove button background transitions to Error color at 40% opacity. Chip body remains unchanged.
- **Release on remove button (160 ms, ease-in)**: Chip animates out: scale reduces to 0, opacity fades to 0. Neighboring chips smoothly reposition to fill the gap (160 ms, ease-in-out). Remaining chips maintain their relative order.
- **Focus (keyboard)**: Focus ring appears 2 px outside the chip boundary. Color: Focus Ring token.

## Chip — Compact (Single-Line with Overflow)
Used in preview contexts and summary headers where space is constrained.
- **Default**: Chips arranged in a single horizontal line. Rightmost chip may be an overflow indicator (`+N more` or `⋯`).
- **Hover-In on visible chip (120 ms, ease-out)**: Identical to Default mode Hover-In.
- **Hover-In on overflow indicator (120 ms, ease-out)**: Overflow indicator background transitions to Accent at 25% opacity. A tooltip or popover appears showing the full list of hidden chips (220 ms fade-in).
- **Overflow Popover**: Appears below the overflow indicator. Contains all hidden chips in a vertical list. Each chip in the popover behaves identically to Default mode. Popover has soft shadow (floating element per §5.9).
- **Popover Dismiss (160 ms, ease-in)**: Triggered by clicking outside or pressing Escape. Popover fades out and scales to 96%.

## Chip — Category-Colored Variant
Used when chips need to communicate category membership (e.g., DNA traits).
- **Default**: Background is category color at 15% opacity. Left accent bar (2 px wide) in full category color. Text is Primary Text.
- **Hover-In (120 ms, ease-out)**: Background transitions to category color at 25% opacity. Accent bar brightens slightly.
- **Selected State**: Not applicable — chips represent already-selected items.

## Chip Removal Animation
When a chip is removed:
1. **Frame 0-80 ms**: Chip scale reduces from 100% to 90%. Opacity reduces from 100% to 70%.
2. **Frame 80-160 ms**: Chip scale reduces from 90% to 0%. Opacity reduces from 70% to 0%.
3. **Frame 0-160 ms (parallel)**: Neighboring chips smoothly reposition to fill the gap. Repositioning uses ease-in-out.
4. **Frame 160+ ms**: Chip is destroyed. Layout is stable.

> Behavior → Applies to: Chips (§6.5)

---

# 8.26 Check Row Behavior Blueprint

Check Rows replace isolated checkboxes with interactive rows. Dataset Composer uses two variants.

## Check Row — List Variant
Used for detailed selections with descriptions and metadata.
- **Default**: Background is transparent. Padding 8 px vertical, 12 px horizontal. Left side contains selection indicator (16 px × 16 px checkbox). Right side contains primary label, optional description, optional metadata. Entire row is clickable.
- **Hover-In (120 ms, ease-out)**: Background transitions to Hover Surface. Checkbox border transitions to Accent at 50% opacity. Cursor changes to pointer.
- **Hover-Out (120 ms, ease-in)**: Background returns to transparent. Checkbox border returns to Border token.
- **Press (80 ms, ease-in)**: Background darkens to Pressed Surface. Checkbox animates selection state change (see below).
- **Click (140 ms, ease-out)**: Checkbox animates from unchecked to checked (or vice versa). Background transitions to Accent at 10% opacity for selected rows, or transparent for unselected. Optional left accent bar (3 px wide, Accent color) fades in along the left edge for selected rows.
- **Focus (keyboard)**: Focus ring appears 2 px inside the row boundary. Color: Focus Ring token.
- **Disabled**: Opacity drops to 40%. Cursor changes to not-allowed. No hover or focus response.

## Check Row — Grid Cell Variant (Compact)
Used for dense tag selections arranged in a grid (e.g., DNA traits).
- **Default**: Background is Card Background. Border 1 px solid Border token. Corner radius 8 px. Padding 8 px on all sides. Contains selection indicator (smaller, 14 px × 14 px) and label text. Minimum width 140 px.
- **Hover-In (120 ms, ease-out)**: Background transitions to Hover Surface. Border transitions to Accent at 50% opacity.
- **Hover-Out (120 ms, ease-in)**: Background returns to Card Background. Border returns to Border token.
- **Click (140 ms, ease-out)**: Selection indicator animates. Background transitions to category color at 15% opacity for selected cells, or Card Background for unselected. Border transitions to category color at 50% opacity for selected cells.
- **Focus (keyboard)**: Focus ring appears 2 px outside the cell boundary.

## Checkbox Animation (shared by both variants)
- **Unchecked → Checked (140 ms, ease-out)**: Checkmark icon scales from 0 to 100%. Checkbox background transitions from transparent to Accent color. Checkbox border transitions from Border token to Accent color.
- **Checked → Unchecked (140 ms, ease-out)**: Checkmark icon scales from 100% to 0. Checkbox background transitions from Accent color to transparent. Checkbox border transitions from Accent color to Border token.
- **Indeterminate (tri-state only, 140 ms, ease-out)**: Horizontal dash icon scales from 0 to 100%. Checkbox background transitions to Accent at 50% opacity. Used in Personality workspace to represent "Avoid" state.

> Behavior → Applies to: Check Rows (§6.7)

---

# 8.27 Empty State Behavior Blueprint

Empty states are intentional interface elements, not failures.

## Empty State — Initial (First-Time Use)
- **Appear (220 ms, ease-out)**: Empty state fades in with a subtle scale animation (96% → 100%). Illustration or icon appears first (140 ms), followed by title (160 ms, 40 ms delay), followed by description (160 ms, 80 ms delay), followed by primary action button (160 ms, 120 ms delay).
- **Visible**: State remains stable. Primary action button pulses once (scale 100% → 105% → 100% over 600 ms) to draw attention, then remains static.
- **Interact with primary action**: Standard button behavior applies. Empty state fades out (160 ms) as content appears.

## Empty State — Filtered (No Results)
- **Appear (160 ms, ease-in)**: When a filter produces no results, the previous content fades out (120 ms) and the empty state fades in (160 ms). Layout remains stable — no jumps.
- **Visible**: State remains stable. Primary action (if any, e.g., "Clear Filters") is immediately available.
- **Filter Cleared**: Empty state fades out (120 ms). Previous content fades back in (160 ms).

## Empty State — Error (Failed to Load)
- **Appear (220 ms, ease-out)**: Error state fades in with subtle scale (96% → 100%). Error icon appears first, followed by title, description, and retry button (same staggered timing as Initial state).
- **Retry Click**: Retry button enters loading state (spinner appears, text changes to "Retrying..."). If successful, error state fades out and content appears. If failed, error state remains with updated message.

> Behavior → Applies to: Empty States (§6.16)

---

# 8.28 Loading State Behavior Blueprint

Loading states preserve layout stability and communicate progress.

## Skeleton Placeholder
- **Appear (160 ms, ease-in)**: Skeleton elements fade in. Each skeleton element has a shimmer animation: a light gradient moves from left to right across the element.
- **Shimmer Animation (continuous)**: Gradient moves from left to right over 1500 ms. Uses linear easing. Repeats indefinitely until content loads.
- **Content Replace (200 ms, ease-out)**: When content is ready, skeleton fades out (120 ms). Content fades in (160 ms, 40 ms delay). Layout remains stable — no jumps.

## Inline Loading Indicator
- **Appear (120 ms, ease-in)**: Small spinner fades in at the location where content will appear.
- **Spin (continuous)**: Spinner rotates continuously. Rotation uses linear easing. Duration: 1000 ms per full rotation.
- **Disappear (120 ms, ease-out)**: When content is ready, spinner fades out. Content fades in (140 ms).

## Progress Bar
- **Appear (160 ms, ease-in)**: Progress bar fades in. Initial fill is 0%.
- **Progress Update (continuous)**: Fill width animates smoothly to new value. Uses ease-out easing. Duration: 200 ms per update.
- **Complete (220 ms, ease-out)**: Fill reaches 100%. Bar briefly flashes to Success color (120 ms), then fades out (100 ms). Success message or content appears.

> Behavior → Applies to: Loading States (§6.17)

---

# 8.29 Context Menu Behavior Blueprint

Context menus expose secondary functionality without cluttering the interface.

## Appear (140 ms, ease-out)
- Menu panel fades in (opacity 0 → 1).
- Menu panel scales from 96% → 100%.
- Menu panel appears at the cursor position (or at the triggering element's edge if cursor position would push the menu off-screen).
- Menu panel has soft shadow (floating element per §5.9).
- First item is focused (highlighted with Hover Surface background).

## Visible
- Menu remains stable.
- Arrow keys navigate between items (focus moves with 80 ms transition).
- Enter or Space activates focused item.
- Escape dismisses menu.
- Click outside dismisses menu.

## Item Hover (80 ms, ease-out)
- Item background transitions to Hover Surface.
- Submenu indicator (if any) transitions to Accent color.

## Item Click (120 ms, ease-in)
- Item background transitions to Pressed Surface.
- Menu dismisses (140 ms fade-out, 140 ms scale to 96%).
- Action executes.

## Submenu Appear (140 ms, ease-out)
- Submenu appears to the right of the parent item (or to the left if right edge would push off-screen).
- Submenu fades in and scales from 96% → 100%.
- Parent item remains highlighted.

> Behavior → Applies to: Context Menus (§6.18)

---

# 8.30 Tooltip Behavior Blueprint

Tooltips supplement the interface without overwhelming it.

## Appear (after 400 ms hover delay)
- Tooltip fades in (120 ms, ease-out).
- Tooltip appears near the triggering element (positioned to avoid obscuring the element).
- Tooltip has soft shadow (floating element per §5.9).

## Visible
- Tooltip remains stable as long as the cursor remains on the triggering element.
- Tooltip does not intercept mouse events (clicks pass through to the element below).

## Disappear (80 ms, ease-in)
- Triggered immediately when cursor leaves the triggering element.
- Tooltip fades out.
- No fade-out delay — tooltip disappears instantly to avoid visual clutter.

## Tooltip with Rich Content
- Identical timing to standard tooltip.
- Rich content (multiple lines, icons, formatted text) fades in as a single unit.
- If the tooltip contains interactive elements (rare), it remains visible while the cursor is over the tooltip itself.

> Behavior → Applies to: Tooltips (§6.19)

---

# 8.31 Summary Panel Behavior Blueprint

The Summary Panel is a Dataset Composer-specific component used in the Profiles workspace context panel. It displays a breakdown of the user's current selections.

## Panel Appear (160 ms, ease-in)
- Panel slides in from the right edge (translateX 20 px → 0).
- Panel fades in (opacity 0 → 1).
- Panel has soft shadow (floating element per §5.9).

## Content Update (140 ms, ease-out)
- When the user's selections change, the summary updates dynamically.
- Changed values animate: old value fades out (80 ms), new value fades in (80 ms, 40 ms delay).
- Category counters animate scale (100% → 110% → 100% over 200 ms) when their values change.
- New categories slide in from the right (160 ms).
- Removed categories slide out to the right and fade out (160 ms).

## Category Breakdown Row
- **Default**: Background is transparent. Padding 8 px vertical, 12 px horizontal. Left side contains colored bullet (8 px diameter, filled with category color). Right side contains category name and count.
- **Hover-In (120 ms, ease-out)**: Background transitions to Hover Surface. Cursor changes to pointer. Clicking the row scrolls the main workspace to the corresponding category.
- **Hover-Out (120 ms, ease-in)**: Background returns to transparent.

## Portrait Area
- **Default**: Rounded rectangle (corner radius 12 px) with placeholder icon and "Add portrait" hint text. Background is Hover Surface.
- **With Portrait**: Portrait image fills the area. Aspect ratio preserved. Soft inner shadow for depth.
- **Hover-In on portrait (120 ms, ease-out)**: Slight zoom (scale 100% → 102%). Overlay appears with "Change portrait" and "Remove portrait" actions.
- **Portrait Change (200 ms, ease-in-out)**: Old portrait fades out (100 ms). New portrait fades in (160 ms, 40 ms delay).

## "View Full Summary" Link
- **Default**: Text is Accent color. No underline. Cursor is pointer.
- **Hover-In (120 ms, ease-out)**: Text underlines with animated stroke (left to right, 200 ms).
- **Click**: Expands the summary panel to show all categories (220 ms, ease-in-out). Panel height smoothly increases.

> Behavior → Applies to: Summary Panel (Profiles workspace, §7.7)

---

---

# 9. Accessibility

Accessibility is not an optional feature. It is a fundamental requirement for professional software.

Dataset Composer must be usable by people with diverse abilities, including those who rely on assistive technologies.

---

## 9.1 Core Accessibility Principles

Every interface decision should consider accessibility from the beginning.

Accessibility should never be treated as an afterthought or a checkbox.

The following principles guide accessible design throughout the application.

---

### Inclusive by Default

The interface should work for the widest possible audience without requiring special modes or settings.

Accessible design benefits everyone.

Large click targets help users with motor impairments and users with large displays.

Clear typography helps users with visual impairments and users working in bright environments.

Keyboard navigation helps power users and users who cannot use a mouse.

---

### Multiple Channels

Information should never rely on a single sensory channel.

Color should never be the only way to communicate state.

Examples:

- Error states should use color AND icon AND text
- Selected items should use background color AND border AND visual indicator
- Required fields should use asterisk AND label text AND tooltip

Users with color vision deficiencies must be able to understand the interface without distinguishing colors.

---

### Predictable Behavior

The interface should behave consistently and predictably.

Users should be able to build mental models of how the application works.

Unexpected behavior creates confusion and reduces confidence.

Every interactive element should respond to input in expected ways.

---

### Forgiving Interface

The interface should prevent errors when possible and recover gracefully when they occur.

Destructive actions should require confirmation.

Auto-save should protect against data loss.

Undo should be available for recent actions.

Error messages should explain what went wrong and how to fix it.

---

## 9.2 Keyboard Navigation

Keyboard navigation is essential for accessibility and power users.

Every interactive element must be reachable and operable via keyboard.

---

### Tab Order

Tab order should follow visual layout.

Focus should move logically from top to bottom, left to right.

Tab order should match the expected workflow.

Avoid creating tab traps where focus gets stuck in a region.

---

### Focus Indicators

Focused elements must display a clear visual indicator.

Focus indicators should:

- be visible against all backgrounds;
- have sufficient contrast (minimum 3:1 ratio);
- not rely solely on color;
- appear immediately when focus changes;
- disappear when focus moves away.

Dataset Composer uses a focus ring with the following characteristics:

- 2 px width
- Accent color at 40% opacity
- 2 px offset from element boundary
- Rounded to match element corner radius

---

### Keyboard Shortcuts

Common actions should have keyboard shortcuts.

Shortcuts should be documented and discoverable.

Shortcuts should not conflict with system shortcuts.

Recommended shortcuts:

| Action | Shortcut |
|--------|----------|
| Save | Ctrl+S |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| Delete | Delete |
| Search | Ctrl+F |
| New | Ctrl+N |

---

### Arrow Key Navigation

Arrow keys should navigate within logical groups.

Examples:

- Arrow Up/Down navigates between list items
- Arrow Left/Right navigates between tabs
- Arrow keys navigate within menus and dropdowns

Arrow key navigation should wrap around at boundaries or stop at edges, depending on context.

---

### Enter and Space

Enter and Space should activate focused elements.

Enter should trigger the primary action.

Space should toggle checkboxes and switches.

Both should activate buttons.

---

### Escape Key

Escape should dismiss temporary UI elements.

Examples:

- Close dialogs and modals
- Close dropdowns and menus
- Cancel drag operations
- Clear search fields
- Exit full-screen mode

Escape should never trigger destructive actions.

---

## 9.3 Screen Reader Support

Screen readers allow visually impaired users to navigate the interface using audio feedback.

Dataset Composer should provide meaningful information to screen readers.

---

### Semantic Structure

Use semantic HTML elements where possible.

In PySide6/Qt, this means:

- Use QLabel for text that should be read
- Use QPushButton for actions
- Use QCheckBox for binary choices
- Use QRadioButton for mutually exclusive options
- Use proper heading hierarchy

Avoid using generic widgets for semantic purposes.

---

### Accessible Names

Every interactive element must have an accessible name.

Accessible names should:

- be concise and descriptive;
- start with the most important information;
- avoid redundancy;
- be unique within their context.

Examples:

- Good: "Save Character Profile"
- Bad: "Button"
- Good: "Delete Luna profile"
- Bad: "Delete"

---

### Accessible Descriptions

Complex elements may need accessible descriptions.

Descriptions provide additional context beyond the name.

Use descriptions for:

- explaining non-obvious behavior;
- providing usage instructions;
- describing current state;
- warning about consequences.

---

### Live Regions

Dynamic content updates should be announced to screen readers.

Use live regions for:

- progress indicators;
- status messages;
- validation errors;
- notifications.

Avoid over-announcing. Frequent announcements become noise.

---

### Focus Management

Focus should move logically when the interface changes.

Examples:

- When a dialog opens, focus moves to the first interactive element
- When a dialog closes, focus returns to the trigger element
- When content is added, focus may move to the new content
- When an element is deleted, focus moves to the next logical element

Focus should never disappear or move to unexpected locations.

---

## 9.4 Color and Contrast

Color choices affect readability and accessibility.

Dataset Composer must meet minimum contrast requirements.

---

### Contrast Ratios

Text must have sufficient contrast against its background.

Minimum requirements:

| Text Size | Minimum Contrast Ratio |
|-----------|----------------------|
| Normal text (< 18 px) | 4.5:1 |
| Large text (≥ 18 px or 14 px bold) | 3:1 |
| UI components and graphics | 3:1 |

These ratios ensure readability for users with low vision.

---

### Color Blindness

Approximately 8% of males and 0.5% of females have some form of color vision deficiency.

The most common types are:

- Protanopia (red-blind)
- Deuteranopia (green-blind)
- Tritanopia (blue-blind)

Dataset Composer should:

- avoid red/green distinctions as the only differentiator;
- use patterns, icons, or labels in addition to color;
- test color choices with color blindness simulators;
- provide high contrast mode as an option.

---

### Dark Mode Considerations

Dark mode reduces eye strain in low-light environments.

Dark mode should:

- maintain sufficient contrast;
- avoid pure black backgrounds;
- use slightly desaturated colors;
- preserve information hierarchy.

Dataset Composer uses cool graphite tones with subtle blue tint to create a comfortable dark mode experience.

---

## 9.5 Motion and Animation

Motion affects users differently.

Some users are sensitive to motion and may experience discomfort or disorientation.

---

### Reduced Motion

Respect the user's system preference for reduced motion.

When reduced motion is enabled:

- disable non-essential animations;
- use instant transitions instead of smooth animations;
- preserve essential feedback (e.g., state changes);
- avoid parallax and zoom effects.

Essential animations include:

- progress indicators;
- loading states;
- error feedback.

Non-essential animations include:

- decorative transitions;
- hover effects;
- expand/collapse animations.

---

### Animation Duration

Animations should be fast enough to feel responsive but slow enough to be perceivable.

Recommended durations:

- Instant feedback: 80-120 ms
- Standard transitions: 160-220 ms
- Complex animations: 220-280 ms

Avoid animations longer than 400 ms unless they represent actual progress.

---

### Seizure Safety

Flashing content can trigger seizures in users with photosensitive epilepsy.

Dataset Composer should:

- avoid flashing more than 3 times per second;
- avoid large areas of flashing content;
- provide warnings before content that may flash;
- allow users to disable flashing effects.

---

## 9.6 Touch and Motor Accessibility

Some users have limited motor control or use touch interfaces.

The interface should accommodate diverse input methods.

---

### Touch Targets

Touch targets must be large enough to activate reliably.

Minimum touch target size: 44 px × 44 px

Recommended touch target size: 48 px × 48 px

Touch targets should:

- have adequate spacing (minimum 8 px gap);
- be visually distinct;
- provide clear feedback on activation;
- not require precise cursor placement.

---

### Drag and Drop

Drag and drop should have keyboard alternatives.

Not all users can perform drag operations.

Provide alternative methods:

- context menu actions;
- keyboard shortcuts;
- button-based alternatives.

Drag operations should:

- have large drop targets;
- provide clear visual feedback;
- allow cancellation via Escape;
- support touch gestures.

---

### Timing

Some users need more time to complete actions.

Avoid time limits when possible.

When time limits are necessary:

- allow users to extend or disable them;
- provide warnings before timeout;
- preserve user input if timeout occurs;
- allow users to recover from timeout.

---

## 9.7 Cognitive Accessibility

Cognitive accessibility helps users with learning disabilities, attention deficits, or memory impairments.

---

### Clear Language

Use clear, simple language.

Avoid jargon when possible.

When technical terms are necessary, provide explanations.

Write error messages in plain language.

---

### Consistent Layout

Consistent layout reduces cognitive load.

Users should be able to predict where to find information.

Maintain consistent:

- navigation structure;
- button placement;
- information hierarchy;
- interaction patterns.

---

### Progressive Disclosure

Show information gradually.

Avoid overwhelming users with too much information at once.

Use:

- accordions for detailed information;
- tabs for separate workflows;
- tooltips for supplementary information;
- expandable sections for advanced options.

---

### Error Prevention

Prevent errors before they occur.

Use:

- input validation;
- confirmation dialogs for destructive actions;
- undo functionality;
- auto-save;
- clear labels and instructions.

---

## 9.8 Accessibility Testing

Accessibility should be tested throughout development.

---

### Automated Testing

Use automated tools to catch common issues:

- contrast checkers;
- keyboard navigation testers;
- screen reader simulators;
- accessibility linters.

Automated testing catches approximately 30% of accessibility issues.

---

### Manual Testing

Manual testing is essential for comprehensive coverage.

Test with:

- keyboard only (no mouse);
- screen reader;
- high contrast mode;
- reduced motion mode;
- zoom (200% and 400%).

---

### User Testing

Test with real users who have disabilities.

User testing reveals issues that automated and manual testing miss.

Include users with:

- visual impairments;
- motor impairments;
- cognitive disabilities;
- hearing impairments.

---

## 9.9 Accessibility Checklist

Before release, verify the following:

✓ All interactive elements are keyboard accessible
✓ Focus indicators are visible and clear
✓ Color is not the only way to convey information
✓ Text has sufficient contrast (4.5:1 for normal text, 3:1 for large text)
✓ Touch targets are at least 44 px × 44 px
✓ Animations respect reduced motion preferences
✓ Screen readers can navigate and understand the interface
✓ Error messages are clear and actionable
✓ Time limits can be extended or disabled
✓ Drag and drop has keyboard alternatives

---

# 10. Future Directions

Dataset Composer is designed for long-term evolution.

This section outlines planned features and future enhancements.

---

## 10.1 Multi-Language Support

Dataset Composer currently supports English only.

Future versions will support multiple languages.

---

### Planned Languages

Initial language support:

- English (current)
- Russian
- Japanese
- Chinese (Simplified)
- Spanish

Additional languages may be added based on user demand.

---

### Implementation Approach

Multi-language support will use Qt's translation system.

All user-facing strings will be externalized to translation files.

The Settings workspace will include a Language selector.

Language changes will apply immediately without requiring restart.

---

### Translation Guidelines

When preparing for translation:

- avoid concatenating strings;
- use placeholders for variable content;
- consider text expansion (some languages require 30% more space);
- avoid cultural references that may not translate;
- provide context comments for translators.

---

## 10.2 Plugin System

Dataset Composer may support plugins in future versions.

Plugins would allow users to extend functionality without modifying core code.

---

### Potential Plugin Types

- Custom exporters (new output formats)
- Custom validators (additional validation rules)
- Custom generators (alternative generation algorithms)
- Custom analyzers (specialized analysis tools)
- Integration plugins (connection to external services)

---

### Plugin Architecture

Plugins would use a sandboxed architecture:

- plugins run in isolated processes;
- plugins have limited access to the filesystem;
- plugins communicate via defined APIs;
- plugins can be enabled/disabled without restart;
- plugins can be installed from a marketplace.

---

### Security Considerations

Plugins introduce security risks.

Mitigation strategies:

- code signing for official plugins;
- permission system for plugin capabilities;
- sandboxing to prevent unauthorized access;
- user confirmation before installing plugins;
- automatic updates for security patches.

---

## 10.3 Cloud Synchronization

Future versions may support cloud synchronization.

Cloud sync would allow users to work across multiple devices.

---

### Synchronized Data

The following data would sync:

- character profiles;
- scene rules;
- prompt library customizations;
- application settings;
- generation history.

Large files (generated datasets) would not sync by default.

---

### Sync Options

Users could choose:

- automatic sync (continuous background sync);
- manual sync (sync on demand);
- selective sync (choose which profiles to sync);
- offline mode (work without internet connection).

---

### Conflict Resolution

When conflicts occur:

- show both versions side by side;
- allow manual merging;
- provide automatic merge for non-conflicting changes;
- keep version history for recovery.

---

## 10.4 Collaboration Features

Future versions may support real-time collaboration.

Multiple users could work on the same project simultaneously.

---

### Collaboration Scenarios

- team members editing different profiles simultaneously;
- real-time preview of changes;
- comments and annotations;
- change tracking and approval workflows;
- role-based permissions (viewer, editor, admin).

---

### Technical Requirements

Real-time collaboration requires:

- WebSocket connections for live updates;
- operational transformation for conflict resolution;
- presence indicators (who is online);
- cursor sharing (see where others are working);
- chat or commenting system.

---

## 10.5 Advanced Analytics

Future versions may include advanced analytics features.

---

### Planned Analytics

- tag co-occurrence analysis (which tags appear together);
- coverage heatmaps (visual representation of coverage);
- quality scoring (automated quality assessment);
- trend analysis (how coverage changes over time);
- comparative analysis (compare multiple datasets).

---

### Visualization

Analytics would use:

- interactive charts;
- filterable tables;
- exportable reports;
- customizable dashboards.

---

## 10.6 Integration with Generation Tools

Future versions may integrate directly with image generation tools.

---

### Potential Integrations

- Kohya_ss (direct training initiation)
- OneTrainer (direct training initiation)
- Stable Diffusion WebUI (automatic image generation)
- ComfyUI (workflow integration)
- Civitai (model publishing)

---

### Integration Benefits

- one-click training;
- automatic image generation;
- visual preview of generated images;
- quality assessment of generated images;
- iterative refinement (generate, assess, adjust rules, regenerate).

---

## 10.7 Mobile Companion App

A mobile companion app may be developed in the future.

The mobile app would allow users to:

- view profiles and rules;
- make quick edits;
- monitor generation progress;
- receive notifications;
- review generated datasets.

Full editing capabilities would remain in the desktop application.

---

## 10.8 Machine Learning Assistance

Future versions may incorporate machine learning to assist users.

---

### Potential ML Features

- automatic tag suggestions based on context;
- intelligent rule recommendations;
- anomaly detection (find unusual tag combinations);
- coverage prediction (predict coverage before generation);
- natural language rule creation (describe rules in plain language).

---

### User Control

ML features would always be optional.

Users would have full control:

- enable/disable individual ML features;
- review and approve ML suggestions;
- provide feedback to improve suggestions;
- work without ML assistance.

---

# 11. Design Tokens

Design Tokens are the atomic values that define the visual identity of Dataset Composer. They translate the philosophical principles from Chapter 5 into concrete, implementation-ready specifications.

Tokens are organized into six categories:
- Color Tokens
- Typography Tokens
- Spacing Tokens
- Radius Tokens
- Easing Tokens
- Category Color Tokens

All tokens should be defined as constants in a central configuration file and referenced throughout the codebase. This ensures that any visual change propagates consistently across the entire application.

---

## 11.1 Color Tokens

The color system is built on cool graphite-blue tones with a subtle blue tint, avoiding pure black. Accent colors are used sparingly and only for interactive elements.

### Base Palette

| Token Name | Hex Value | Usage |
|---|---|---|
| `color-window-bg` | `#1a1d23` | Main application window background |
| `color-workspace-bg` | `#1f2329` | Workspace content area background |
| `color-sidebar-bg` | `#1a1d23` | Sidebar and navigation background |
| `color-card-bg` | `#252a33` | Card surface background |
| `color-card-elevated` | `#2d333d` | Elevated card background (selected state) |
| `color-hover-surface` | `#2d333d` | Hover state background |
| `color-pressed-surface` | `#353b47` | Pressed state background |
| `color-border` | `#3a4150` | Subtle borders and dividers |
| `color-border-strong` | `#4a5264` | Stronger borders (inputs, focus) |
| `color-divider` | `#2d333d` | Section dividers |

### Text Colors

| Token Name | Hex Value | Usage |
|---|---|---|
| `color-text-primary` | `#e8eaf0` | Primary readable text |
| `color-text-secondary` | `#9aa3b8` | Descriptions, metadata, placeholders |
| `color-text-disabled` | `#5a6378` | Disabled state text |
| `color-text-inverse` | `#1a1d23` | Text on accent backgrounds |

### Accent Colors

| Token Name | Hex Value | Usage |
|---|---|---|
| `color-accent` | `#4f6df5` | Primary interactive accent (indigo-blue) |
| `color-accent-hover` | `#6b85f7` | Hover state for accent elements |
| `color-accent-pressed` | `#3d5ae0` | Pressed state for accent elements |
| `color-accent-subtle` | `#4f6df5` at 15% opacity | Subtle accent backgrounds (chips, badges) |
| `color-accent-hover-subtle` | `#4f6df5` at 25% opacity | Hover state for subtle accent backgrounds |

### Semantic Colors

| Token Name | Hex Value | Usage |
|---|---|---|
| `color-success` | `#3dd68c` | Success states, confirmations |
| `color-success-subtle` | `#3dd68c` at 15% opacity | Success backgrounds |
| `color-warning` | `#f5a623` | Warning states, caution messages |
| `color-warning-subtle` | `#f5a623` at 15% opacity | Warning backgrounds |
| `color-error` | `#f5475b` | Error states, destructive actions |
| `color-error-subtle` | `#f5475b` at 15% opacity | Error backgrounds |

### Selection and Focus

| Token Name | Hex Value | Usage |
|---|---|---|
| `color-selection` | `#4f6df5` at 30% opacity | Selected item background |
| `color-focus-ring` | `#4f6df5` at 40% opacity | Keyboard focus indicator |

---

## 11.2 Typography Tokens

Typography establishes hierarchy through size, weight and line-height rather than color alone.

### Font Family

| Token Name | Value | Usage |
|---|---|---|
| `font-family-primary` | `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` | All interface text |
| `font-family-mono` | `"JetBrains Mono", "Fira Code", "Consolas", monospace` | Code, logs, technical data |

### Font Sizes

| Token Name | Size (px) | Usage |
|---|---|---|
| `font-size-window-title` | `20` | Window-level headings |
| `font-size-section-title` | `16` | Workspace section headings |
| `font-size-category-title` | `14` | Card and accordion headings |
| `font-size-body` | `13` | Default readable content |
| `font-size-secondary` | `12` | Descriptions, supporting text |
| `font-size-caption` | `11` | Metadata, helper labels, badges |

### Font Weights

| Token Name | Weight | Usage |
|---|---|---|
| `font-weight-regular` | `400` | Body text, descriptions |
| `font-weight-medium` | `500` | Emphasized text, labels |
| `font-weight-semibold` | `600` | Headings, buttons, important labels |
| `font-weight-bold` | `700` | Window titles, strong emphasis |

### Line Heights

| Token Name | Value | Usage |
|---|---|---|
| `line-height-tight` | `1.2` | Headings, compact text |
| `line-height-normal` | `1.5` | Body text, readable content |
| `line-height-relaxed` | `1.7` | Long-form descriptions, help text |

---

## 11.3 Spacing Tokens

All spacing values derive from a 4 px base unit. This creates consistent rhythm throughout the interface.

### Spacing Scale

| Token Name | Value (px) | Usage |
|---|---|---|
| `space-1` | `4` | Tight spacing between related elements |
| `space-2` | `8` | Default spacing between controls |
| `space-3` | `12` | Spacing between grouped sections |
| `space-4` | `16` | Card internal padding, section separation |
| `space-5` | `20` | Larger section separation |
| `space-6` | `24` | Workspace-level spacing |
| `space-8` | `32` | Major section breaks |
| `space-12` | `48` | Page-level margins, hero sections |

### Common Patterns

| Pattern | Value | Description |
|---|---|---|
| Card padding | `space-4` (16 px) | Internal padding for all cards |
| Accordion header padding | `space-3` vertical, `space-4` horizontal | Accordion header internal spacing |
| Button padding | `space-2` vertical, `space-4` horizontal | Standard button internal spacing |
| Input field padding | `space-2` vertical, `space-3` horizontal | Input field internal spacing |
| Chip padding | `space-1` vertical, `space-3` horizontal | Chip internal spacing |

---

## 11.4 Radius Tokens

Rounded corners are a defining characteristic of the Dataset Composer visual identity. Different component types use specific radius values to maintain cohesion.

### Radius Scale

| Token Name | Value (px) | Usage |
|---|---|---|
| `radius-small` | `8` | Small controls (checkboxes, toggles) |
| `radius-medium` | `10` | Buttons, input fields, dropdowns |
| `radius-large` | `12` | Cards, panels, containers |
| `radius-xlarge` | `14` | Dialogs, modals, floating elements |
| `radius-full` | `9999` | Chips, badges, circular elements |

### Application Rules

- **Buttons**: `radius-medium` (10 px)
- **Input fields**: `radius-medium` (10 px)
- **Cards**: `radius-large` (12 px)
- **Dialogs**: `radius-xlarge` (14 px)
- **Chips**: `radius-full` (fully rounded)
- **Checkboxes**: `radius-small` (8 px)
- **Accordion headers**: `radius-large` (12 px)

---

## 11.5 Easing Tokens

Animation easing curves define the character of motion. Dataset Composer uses three primary curves to maintain consistency.

### Easing Curves

| Token Name | Cubic Bezier | Usage |
|---|---|---|
| `ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Elements entering the screen (fade-in, slide-in, expand) |
| `ease-in` | `cubic-bezier(0.55, 0.085, 0.68, 0.53)` | Elements leaving the screen (fade-out, slide-out, collapse) |
| `ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Continuous motion, state transitions |
| `ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful, bouncy interactions (rare, for emphasis) |

### Timing Groups

Referenced from §8.2 Animation Timing.

| Token Name | Duration (ms) | Usage |
|---|---|---|
| `duration-instant` | `80` | Press feedback, immediate state changes |
| `duration-fast` | `120` | Hover transitions, icon appearance |
| `duration-normal` | `160` | Selection, focus, standard transitions |
| `duration-slow` | `220` | Expand/collapse, dialog appearance |
| `duration-slower` | `280` | Complex animations, workspace transitions |

---

## 11.6 Category Color Tokens

Category colors provide visual distinction for different types of content. They are used primarily in the Profiles workspace for DNA categories, but may be applied elsewhere when categorical distinction improves comprehension.

### DNA Category Colors

These colors are used for DNA trait categories in the Profiles workspace. Each category receives a distinct hue to aid visual scanning and recognition.

| Category | Token Name | Hex Value | Subtle Variant (15% opacity) |
|---|---|---|---|
| Face | `color-category-face` | `#a78bfa` | `#a78bfa` at 15% |
| Hair | `color-category-hair` | `#34d399` | `#34d399` at 15% |
| Eyes | `color-category-eyes` | `#fbbf24` | `#fbbf24` at 15% |
| Body | `color-category-body` | `#f472b6` | `#f472b6` at 15% |
| Skin | `color-category-skin` | `#fb923c` | `#fb923c` at 15% |

### Application

Category colors are applied in the following contexts:

- **Accordion category cards**: Left accent bar and category icon badge use the full category color
- **Selected chips**: Background uses the subtle variant (15% opacity), left accent bar uses full color
- **Category counters**: Badge background uses subtle variant, text uses full color
- **Check row selection**: When a check row is selected within a category, the selection indicator and accent bar use the category color

### Other Workspace Categories

For workspaces beyond Profiles, category colors may be defined as needed:

| Context | Suggested Approach |
|---|---|
| **Outfits** (Profiles) | Single neutral accent color or color by subcategory (topwear, bottomwear, etc.) |
| **Personality** (Profiles) | Semantic colors: success for "prefer", error for "avoid" |
| **Atmosphere** (Profiles) | Distinct colors for lighting vs. weather |
| **Library** | Category colors by asset type (locations, actions, props, etc.) |

When introducing new category color schemes, ensure they:
- Do not conflict with the primary accent color
- Maintain sufficient contrast against card backgrounds
- Remain distinguishable for users with color vision deficiencies (pair with icons or labels when possible)

---

## 11.7 Token Implementation Strategy

Design Tokens should be implemented as a centralized configuration that feeds both the QSS stylesheet and the Python code.

### Recommended Architecture

src/
├── ui_qt/
│ ├── theme.py # Token constants (Python)
│ ├── theme.qss # Generated or manually maintained QSS using token values
│ └── ...

### theme.py Structure

```python
"""
Design Tokens for Dataset Composer UI.
All visual constants are defined here and referenced throughout the codebase.
"""

# === Color Tokens ===
class Colors:
    WINDOW_BG = "#1a1d23"
    WORKSPACE_BG = "#1f2329"
    SIDEBAR_BG = "#1a1d23"
    CARD_BG = "#252a33"
    CARD_ELEVATED = "#2d333d"
    HOVER_SURFACE = "#2d333d"
    PRESSED_SURFACE = "#353b47"
    BORDER = "#3a4150"
    BORDER_STRONG = "#4a5264"
    DIVIDER = "#2d333d"
    
    TEXT_PRIMARY = "#e8eaf0"
    TEXT_SECONDARY = "#9aa3b8"
    TEXT_DISABLED = "#5a6378"
    TEXT_INVERSE = "#1a1d23"
    
    ACCENT = "#4f6df5"
    ACCENT_HOVER = "#6b85f7"
    ACCENT_PRESSED = "#3d5ae0"
    ACCENT_SUBTLE = "rgba(79, 109, 245, 0.15)"
    ACCENT_HOVER_SUBTLE = "rgba(79, 109, 245, 0.25)"
    
    SUCCESS = "#3dd68c"
    SUCCESS_SUBTLE = "rgba(61, 214, 140, 0.15)"
    WARNING = "#f5a623"
    WARNING_SUBTLE = "rgba(245, 166, 35, 0.15)"
    ERROR = "#f5475b"
    ERROR_SUBTLE = "rgba(245, 71, 91, 0.15)"
    
    SELECTION = "rgba(79, 109, 245, 0.30)"
    FOCUS_RING = "rgba(79, 109, 245, 0.40)"

# === Category Colors ===
class CategoryColors:
    FACE = "#a78bfa"
    FACE_SUBTLE = "rgba(167, 139, 250, 0.15)"
    HAIR = "#34d399"
    HAIR_SUBTLE = "rgba(52, 211, 153, 0.15)"
    EYES = "#fbbf24"
    EYES_SUBTLE = "rgba(251, 191, 36, 0.15)"
    BODY = "#f472b6"
    BODY_SUBTLE = "rgba(244, 114, 182, 0.15)"
    SKIN = "#fb923c"
    SKIN_SUBTLE = "rgba(251, 146, 60, 0.15)"

# === Spacing Tokens ===
class Spacing:
    SPACE_1 = 4
    SPACE_2 = 8
    SPACE_3 = 12
    SPACE_4 = 16
    SPACE_5 = 20
    SPACE_6 = 24
    SPACE_8 = 32
    SPACE_12 = 48

# === Radius Tokens ===
class Radius:
    SMALL = 8
    MEDIUM = 10
    LARGE = 12
    XLARGE = 14
    FULL = 9999

# === Typography Tokens ===
class Typography:
    FONT_PRIMARY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
    
    SIZE_WINDOW_TITLE = 20
    SIZE_SECTION_TITLE = 16
    SIZE_CATEGORY_TITLE = 14
    SIZE_BODY = 13
    SIZE_SECONDARY = 12
    SIZE_CAPTION = 11
    
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700

# === Easing Tokens ===
class Easing:
    EASE_OUT = "cubic-bezier(0.16, 1, 0.3, 1)"
    EASE_IN = "cubic-bezier(0.55, 0.085, 0.68, 0.53)"
    EASE_IN_OUT = "cubic-bezier(0.65, 0, 0.35, 1)"
    EASE_SPRING = "cubic-bezier(0.34, 1.56, 0.64, 1)"

# === Duration Tokens ===
class Duration:
    INSTANT = 80
    FAST = 120
    NORMAL = 160
    SLOW = 220
    SLOWER = 280

```
---

### Usage in Code
When building UI components, reference tokens rather than hardcoding values:

``` python 
from ui_qt.theme import Colors, Spacing, Radius

# Instead of:
button.setStyleSheet("background-color: #4f6df5; padding: 8px 16px; border-radius: 10px;")

# Use:
button.setStyleSheet(f"""
    background-color: {Colors.ACCENT};
    padding: {Spacing.SPACE_2}px {Spacing.SPACE_4}px;
    border-radius: {Radius.MEDIUM}px;
""")
```
---

### QSS Integration

The theme.qss file should use the same token values. While QSS cannot directly import Python constants, the values should be kept in sync manually or through a build script.
Example QSS using token values:

``` css
QPushButton {
    background-color: #4f6df5;
    padding: 8px 16px;
    border-radius: 10px;
    color: #e8eaf0;
}

```
---

## 11.8 Token Maintenance
Design Tokens are a living system. As the application evolves, tokens may be added, adjusted or deprecated.

### Rules for Token Changes

- Never delete a token without deprecation. Mark deprecated tokens with a comment and provide a migration path.
- Changes propagate globally. Adjusting a token value affects every component that uses it. Review the impact before committing.
- New tokens must be documented. Every new token should include a usage description and example.
- Semantic tokens take precedence over raw values. Always use Colors.ACCENT rather than #4f6df5 in code.
- Category colors require approval. Adding new category color schemes should be reviewed to ensure they do not conflict with existing palettes.

### Versioning

Token changes should be tracked in the document changelog (Appendix). Major palette shifts or typography changes should increment the document version.

---

# 12. Appendix

This appendix provides reference information for designers and developers.

---

## 12.1 Glossary

Key terms used throughout this document.

---

### A

**Accessibility**
The practice of making software usable by people with diverse abilities, including those who rely on assistive technologies.

**Accordion**
A collapsible UI component that organizes related information into expandable sections. Replaces large trees with cleaner, more approachable organization.

**Accent Color**
The primary interactive color used for buttons, links, focus indicators and selected states. Used sparingly to maintain visual hierarchy.

---

### B

**Behavior Blueprint**
A frame-by-frame specification of how a component responds to user input. Defines timing, easing and visual changes for each interaction state.

**Border**
A visual line that defines the boundary of an element. Used sparingly in Dataset Composer, primarily for editable controls and focus states.

---

### C

**Card**
A visually independent container that groups related information. Cards replace traditional GroupBoxes and create natural hierarchy.

**Check Row**
An interactive row that replaces isolated checkboxes. The entire row is clickable and responds to hover, making selection more comfortable.

**Chip**
A compact element representing a selected item. Chips are removable and wrap automatically to prevent horizontal scrolling.

**Color Role**
A semantic color assignment (e.g., "Accent", "Error", "Hover Surface") rather than a specific hex value. Roles remain stable while specific colors may evolve.

**Component**
A reusable interface element defined in the Component Library. Components should be consistent throughout the application.

**Context Panel**
A right-side panel that provides contextual information about the current selection or workspace. Updates dynamically based on user actions.

**Coverage**
A statistical measure of how well a dataset represents different characteristics (locations, actions, outfits, etc.).

---

### D

**Dataset**
A collection of scenes used for training AI models. Not a collection of prompts, but a collection of Scene objects.

**Design Token**
An atomic design value (color, spacing, typography) that can be referenced throughout the codebase. Tokens ensure consistency and simplify maintenance.

**Dialog**
A modal window that interrupts the workflow to request user input or display important information. Used sparingly to avoid disruption.

---

### E

**Easing**
The acceleration curve of an animation. Determines how motion starts, progresses and stops. Dataset Composer uses ease-out, ease-in and ease-in-out curves.

**Empty State**
The appearance of a workspace or component when it contains no content. Empty states should guide users toward the next action.

**Expand/Collapse**
The animation of showing or hiding content within an accordion or expandable section. Should preserve spatial continuity.

---

### F

**Focus Ring**
A visual indicator showing which element has keyboard focus. Essential for keyboard navigation and accessibility.

---

### H

**Hover Surface**
The background color applied when a user hovers over an interactive element. Provides feedback that the element is interactive.

---

### I

**Icon**
A visual symbol that supports recognition. Icons should be simple, lightweight and visually neutral. Never decorative.

---

### L

**Loading State**
The appearance of a component while content is being loaded. Should preserve layout stability and communicate progress.

---

### M

**Motion System**
The collection of animation principles, timing groups and behavior blueprints that define how the interface responds to user input.

---

### N

**Notification**
A message that communicates progress or results without interrupting work. Preferred order: Toast → Inline Message → Modal Dialog.

---

### P

**Pressed Surface**
The background color applied when a user presses an interactive element. Provides tactile feedback.

**Primary Text**
The main text color used for readable content. Should have high contrast against backgrounds.

**Progressive Disclosure**
The practice of showing information gradually as it becomes relevant, rather than overwhelming users with everything at once.

---

### R

**Radius**
The corner rounding applied to UI elements. Different component types use specific radius values to maintain visual consistency.

---

### S

**Scene**
The central creative unit of Dataset Composer. A scene represents a single image with all its characteristics (character, outfit, location, action, etc.).

**Secondary Text**
A lighter text color used for descriptions, metadata and supporting information. Provides visual hierarchy without competing with primary content.

**Semantic Color**
A color with meaning (e.g., Success, Warning, Error) rather than purely decorative color. Semantic colors communicate state and importance.

**Shadow**
A visual effect that creates the illusion of elevation. Used sparingly in Dataset Composer, primarily for floating elements like dialogs and menus.

**Sidebar**
A left-side navigation panel that provides access to different workspaces or sections. Should remain calm and visually unobtrusive.

**Spacing**
The distance between UI elements. Dataset Composer uses a 4 px base unit with preferred values: 4, 8, 12, 16, 24, 32, 48 px.

---

### T

**Tab**
A navigation element that switches between different views or workspaces. Active tabs should be immediately recognizable.

**Toast**
A temporary notification that appears at the edge of the screen and disappears automatically. Used for non-critical information.

**Toggle**
A switch that represents persistent application state. Should not be confused with checkboxes, which represent item selection.

**Tooltip**
A small popup that provides supplementary information about an element. Should explain, not compensate for poor design.

---

### V

**Visual Hierarchy**
The arrangement of elements to communicate importance and relationships. Established through spacing, typography and contrast rather than decoration.

**Visual Language**
The collection of visual rules (colors, typography, spacing, etc.) that define the Dataset Composer interface. Ensures consistency across all workspaces.

---

### W

**Whitespace**
Empty space between UI elements. An active design element that improves readability and creates visual breathing room.

**Workspace**
A dedicated environment for completing a specific creative task (Profiles, Library, Generate, Analyzer, Settings). Each workspace has its own purpose but shares the same visual language.

---

## 12.2 Component Index

Quick reference for all components defined in this document.

---

### Interactive Components

| Component | Section | Behavior Blueprint |
|-----------|---------|-------------------|
| Primary Button | 6.2 | 8.22.1 |
| Secondary Button | 6.2 | 8.22.1 |
| Ghost Button | 6.2 | 8.22.1 |
| Icon Button | 6.2 | 8.22.1 |
| Danger Button | 6.2 | 8.22.1 |
| Input Field | 6.8 | 8.22.2 |
| Search Field | 6.6 | 8.22.3 |
| Dropdown | 6.9 | 8.22.4 |
| Toggle Control | 6.10 | 8.22.5 |
| Tab | 6.11 | 8.22.6 |
| Sidebar Item | 6.12 | 8.22.7 |
| Dialog | 6.14 | 8.22.8 |
| Toast Notification | 6.15 | 8.22.9 |

---

### Container Components

| Component | Section | Behavior Blueprint |
|-----------|---------|-------------------|
| Card | 6.3 | 8.23 |
| Accordion | 6.4 | 8.24 |
| Chip | 6.5 | 8.25 |
| Check Row | 6.7 | 8.26 |

---

### State Components

| Component | Section | Behavior Blueprint |
|-----------|---------|-------------------|
| Empty State | 6.16 | 8.27 |
| Loading State | 6.17 | 8.28 |
| Context Menu | 6.18 | 8.29 |
| Tooltip | 6.19 | 8.30 |

---

### Workspace-Specific Components

| Component | Section | Behavior Blueprint |
|-----------|---------|-------------------|
| Summary Panel | 7.7 | 8.31 |

---

## 12.3 Reference Mockups

The following mockups serve as visual references for the design system.

---

### DNA Workspace Reference

The DNA workspace mockup demonstrates:

- three-column layout (sidebar, main workspace, context panel);
- accordion cards for categories;
- chip-based selection display;
- search with instant filtering;
- context panel with character portrait and summary.

This mockup establishes the visual standard for all workspaces.

Other workspaces should match this level of polish and attention to detail.

---

## 12.4 Design Resources

External resources referenced in this document.

---

### Icon Family

Dataset Composer uses Material Design Icons (MDI).

- Website: https://materialdesignicons.com/
- Style: outlined, 24 px base size
- Stroke width: consistent across all icons
- License: SIL Open Font License 1.1

---

### Typography

Dataset Composer uses Inter font family.

- Website: https://rsms.me/inter/
- Weights: Regular (400), Medium (500), Semibold (600), Bold (700)
- License: SIL Open Font License 1.1

Fallback fonts:

- Windows: Segoe UI
- macOS: -apple-system, BlinkMacSystemFont
- Linux: sans-serif

---

### Color Tools

Recommended tools for color selection and contrast checking:

- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Coolors: https://coolors.co/
- Adobe Color: https://color.adobe.com/
- Color Oracle (color blindness simulator): https://colororacle.org/

---

### Accessibility Testing Tools

Recommended tools for accessibility testing:

- axe DevTools: https://www.deque.com/axe/
- WAVE: https://wave.webaim.org/
- NVDA (screen reader): https://www.nvaccess.org/
- VoiceOver (macOS screen reader): built-in
- Chrome DevTools Accessibility panel: built-in

---

## 12.5 Document Changelog

Track changes to this design system document.

---

### Version 1.0 (Draft)

**Date:** 2026

**Changes:**

- Initial document creation
- Defined product philosophy and UI philosophy
- Established 8 core design principles
- Defined visual language (colors, typography, spacing, radius)
- Created component library with 20 components
- Defined 5 workspaces with layout specifications
- Established motion system with behavior blueprints
- Added accessibility guidelines
- Outlined future directions
- Created appendix with glossary and references

**Authors:**

- Vasily Taran (product owner)
- Design system documentation

---

### Future Versions

Future versions will track:

- new components added
- components modified
- tokens added or changed
- workspaces added or modified
- accessibility improvements
- breaking changes

Major changes should increment the version number.

Minor additions and clarifications may use patch versions (1.0.1, 1.0.2, etc.).

---

## 12.6 Contact and Feedback

This document is a living specification.

Feedback and suggestions are welcome.

---

### Reporting Issues

If you find inconsistencies, errors or areas for improvement:

1. Check the latest version of this document
2. Review related sections for context
3. Document the specific issue with examples
4. Suggest a resolution if possible
5. Submit feedback to the project maintainer

---

### Contributing

Contributions to this document should:

- follow the existing format and style;
- include rationale for changes;
- provide examples or mockups when applicable;
- consider impact on existing components and workspaces;
- maintain consistency with established principles.

---

### Questions

For questions about this design system:

- Review the glossary (12.1) for terminology
- Check the component index (12.2) for quick reference
- Examine reference mockups (12.3) for visual examples
- Consult the main README for project overview

---

**End of Document**

This design system document is the single source of truth for the Dataset Composer user interface.

All design and implementation decisions should reference this document to ensure consistency and quality.

The interface should evolve over time, but always within the framework established here.

Consistency builds confidence. Confidence increases productivity.