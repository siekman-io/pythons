<?php
$host = 'localhost';
$user = 'username';
$password = 'password';
$database = 'databasename';

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$websiteFilter = isset($_GET['website']) ? $_GET['website'] : '';
$dateStart = isset($_GET['date_start']) ? $_GET['date_start'] : '';
$dateEnd = isset($_GET['date_end']) ? $_GET['date_end'] : '';

$query = "SELECT email, websites, received_at FROM subscribers WHERE 1=1";
if ($websiteFilter) {
    $query .= " AND websites LIKE '%$websiteFilter%'";
}
if ($dateStart && $dateEnd) {
    $query .= " AND received_at BETWEEN '$dateStart' AND '$dateEnd'";
}
$query .= " ORDER BY received_at DESC";

$result = $conn->query($query);

if (isset($_GET['export']) && $_GET['export'] == 'true') {
    header('Content-Type: text/plain');
    header('Content-Disposition: attachment; filename="subscribers.txt"');
    while ($row = $result->fetch_assoc()) {
        echo $row['email'] . "\n";
    }
    exit;
}
?>

<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nieuwsbrief Abonnees</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h2>Nieuwsbrief Abonnees</h2>
        <form method="GET" class="mb-3">
            <div class="row">
                <div class="col-md-4">
                    <input type="text" name="website" class="form-control" placeholder="Filter op website" value="<?php echo htmlspecialchars($websiteFilter); ?>">
                </div>
                <div class="col-md-3">
                    <input type="date" name="date_start" class="form-control" value="<?php echo htmlspecialchars($dateStart); ?>">
                </div>
                <div class="col-md-3">
                    <input type="date" name="date_end" class="form-control" value="<?php echo htmlspecialchars($dateEnd); ?>">
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-primary">Filter</button>
                    <a href="?export=true&website=<?php echo urlencode($websiteFilter); ?>&date_start=<?php echo urlencode($dateStart); ?>&date_end=<?php echo urlencode($dateEnd); ?>" class="btn btn-success">Export</a>
                </div>
            </div>
        </form>

        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Email</th>
                    <th>Websites</th>
                    <th>Ingeschreven op</th>
                </tr>
            </thead>
            <tbody>
                <?php while ($row = $result->fetch_assoc()): ?>
                    <tr>
                        <td><?php echo htmlspecialchars($row['email']); ?></td>
                        <td><?php echo htmlspecialchars($row['websites']); ?></td>
                        <td><?php echo htmlspecialchars($row['received_at']); ?></td>
                    </tr>
                <?php endwhile; ?>
            </tbody>
        </table>
    </div>
</body>
</html>
<?php $conn->close(); ?>
