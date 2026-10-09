function Get-ValorRecordedCreationUtc {
    param([object]$Timestamp)
    # PowerShell 7.5 can deserialize JSON timestamps directly to DateTime.
    # Parsing that object's culture-dependent string again can swap day/month.
    if ($Timestamp -is [DateTime]) { return $Timestamp.ToUniversalTime() }
    if ($Timestamp -is [DateTimeOffset]) { return $Timestamp.UtcDateTime }
    if ($Timestamp -isnot [string] -or $Timestamp -notmatch '^\d{4}-\d{2}-\d{2}T.+(Z|[+-]\d{2}:\d{2})$') {
        throw 'The recorded creation time must be an ISO timestamp with a time zone.'
    }
    return [DateTimeOffset]::Parse($Timestamp, [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::None).UtcDateTime
}
