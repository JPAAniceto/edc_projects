<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xhtml" indent="yes"/>
    <xsl:template match="root">

        <table class="sortable">
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Symbol</th>
                    <th class="sorttable_numeric">Price</th>
                </tr>
                </thead>

                <tbody>
                <xsl:for-each select="stock">
                    <tr>
                        <td><xsl:value-of select="name"/></td>
                        <td><xsl:value-of select="symbol"/></td>
                        <td><xsl:value-of select="value"/></td>
                    </tr>
                </xsl:for-each>
                </tbody>
            </table>
    </xsl:template>
</xsl:stylesheet>