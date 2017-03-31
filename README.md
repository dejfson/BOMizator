# BOMizator
Python application to efficiently generate bill of material from KiCAD projects.

How does it work:

Each Kicad project (of new generation) provides a project description with .pro extension. Give to BOMizator either
the .pro filename, or point it to the directory with a Kicad project.

BOMizator will analyse all the schematic files in the project and brings a list of components with their library/value/footprint
combination. User then can doubleclick on one of these three to launch a octopart.com search for the components. He can select
very specific component and drag-drop its description from the web page into the designator field. BOMizator will parse the
content of the web page for additional information and assign to the component (or group of selected components)

Once user assigns all the components, BOMizator brings a list of needed orders, grouped by supplier. This can be used to
fast-paste the ordering data into suppliers web pages to get instant order.

BOMizator allows for each particular component to select ordering quantities in terms of multiplication-addition-rounding, so
user can specify for a given component e.g. I want 3 times more of those components, rounded to nearest hundreds. Or I want
2 more components.

Still in alpha, not all features are currently supported (BOM to PDF not yet works), however as one can use quick paste, 
the application is already usefull.

The application is primarily written in LINUX, however it is tested as well on WINDOWS make it available as well for windows 
users. It requires Python 3.5+ and PyQt5, which is usually shipped via PyPI on both linux and windows.


Comments and pull requests are welcomed.
