<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xhtml" indent="yes"/>
    <xsl:template match="root">

        <table class="sortable">
            <thead>
                <tr>
                    <th>Company</th>
                    <th>Symbol</th>
                </tr>
            </thead>

            <tbody>
            <xsl:for-each select="company">
                    <tr>
                        <td>
                            <a href="/companies/{symbol}"><xsl:value-of select="name"/></a>
                        </td>
                        <td>
                            <a href="/companies/{symbol}"><xsl:value-of select="symbol"/></a>
                        </td>
                        <td>
                            <a class="btn waves-effect waves-light" href="/companies/{symbol}">Buy
                                <i class="material-icons right">business_center</i>
                            </a>
                        </td>
                    </tr>
            </xsl:for-each>

            </tbody>
        </table>
    </xsl:template>
</xsl:stylesheet>