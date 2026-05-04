<?xml version="1.0" encoding="UTF-8"?>
<!--
  GDACS RSS (XML) → Canonical Earthquake XML
  
  Input:  GDACS RSS XML
  Output: <earthquake-dashboard-data> canonical schema
-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"
  xmlns:gdacs="http://www.gdacs.org">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <earthquake-dashboard-data>
      <xsl:apply-templates select="//item[gdacs:eventtype='EQ']"/>
    </earthquake-dashboard-data>
  </xsl:template>

  <xsl:template match="item">
    <event>
      <id><xsl:value-of select="guid"/></id>
      <title><xsl:value-of select="title"/></title>
      <main_time><xsl:value-of select="pubDate"/></main_time>
      <magnitude><xsl:value-of select="gdacs:severity/@value"/></magnitude>
      <magnitude_type>M</magnitude_type>
      <depth_km><xsl:value-of select="substring-before(substring-after(gdacs:severity, 'Depth:'), 'km')"/></depth_km>
      <latitude><xsl:value-of select="geo:Point/geo:lat"/></latitude>
      <longitude><xsl:value-of select="geo:Point/geo:long"/></longitude>
      <place>
        <xsl:choose>
          <xsl:when test="gdacs:location != ''"><xsl:value-of select="gdacs:location"/></xsl:when>
          <xsl:otherwise>Earthquake in <xsl:value-of select="gdacs:country"/></xsl:otherwise>
        </xsl:choose>
      </place>
      <country><xsl:value-of select="gdacs:country"/></country>
      <alert_level><xsl:value-of select="gdacs:alertlevel"/></alert_level>
      <alert_score><xsl:value-of select="gdacs:alertscore"/></alert_score>
      <tsunami><xsl:value-of select="gdacs:tsunami_alert"/></tsunami>
      <felt></felt>
      <status><xsl:value-of select="gdacs:episodealertlevel"/></status>
      <source>GDACS</source>
      <link><xsl:value-of select="link"/></link>
      <severity_text><xsl:value-of select="gdacs:severity"/></severity_text>
      <population_text><xsl:value-of select="gdacs:population"/></population_text>
    </event>
  </xsl:template>

</xsl:stylesheet>
