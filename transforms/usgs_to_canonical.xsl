<?xml version="1.0" encoding="UTF-8"?>
<!--
  USGS QuakeML → Canonical Earthquake XML
  
  MANDATORY GRADED DELIVERABLE
  Authoritative intermediate transformation for the Global Earthquake Monitor.
  
  Input:  USGS QuakeML (XML)
  Output: <earthquake-dashboard-data> canonical schema
-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:q="http://quakeml.org/xmlns/quakeml/1.2"
  xmlns:bed="http://quakeml.org/xmlns/bed/1.2">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <earthquake-dashboard-data>
      <xsl:apply-templates select="//bed:event"/>
    </earthquake-dashboard-data>
  </xsl:template>

  <xsl:template match="bed:event">
    <event>
      <id><xsl:value-of select="@publicID"/></id>
      <title><xsl:value-of select="bed:description/bed:text"/></title>
      <main_time><xsl:value-of select="bed:origin/bed:time/bed:value"/></main_time>
      <magnitude><xsl:value-of select="bed:magnitude/bed:mag/bed:value"/></magnitude>
      <magnitude_type><xsl:value-of select="bed:magnitude/bed:type"/></magnitude_type>
      <depth_km><xsl:value-of select="round(bed:origin/bed:depth/bed:value div 1000)"/></depth_km>
      <latitude><xsl:value-of select="bed:origin/bed:latitude/bed:value"/></latitude>
      <longitude><xsl:value-of select="bed:origin/bed:longitude/bed:value"/></longitude>
      <place><xsl:value-of select="bed:description/bed:text"/></place>
      <country>Unknown</country> <!-- Extracted via Python during parsing if needed -->
      <alert_level>Unknown</alert_level> <!-- Derived from magnitude in Python -->
      <alert_score><xsl:value-of select="bed:magnitude/bed:mag/bed:value"/></alert_score>
      <tsunami>0</tsunami> <!-- USGS QuakeML doesn't explicitly flag tsunami in this simplified view -->
      <felt><xsl:value-of select="bed:felt"/></felt>
      <status><xsl:value-of select="bed:type"/></status>
      <source>USGS</source>
      <link><xsl:value-of select="@publicID"/></link> <!-- Often the same as ID -->
      <severity_text></severity_text>
      <population_text></population_text>
    </event>
  </xsl:template>

</xsl:stylesheet>
